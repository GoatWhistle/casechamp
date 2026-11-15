import json
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[2]
MAIN = Path(os.environ.get("ROAD_CAPACITY_SOURCE_ROOT", ROOT))
sys.path[:0] = [str(ROOT / "etl"), str(MAIN / "etl"), str(MAIN / "backend/src")]

from road_capacity.activate import activate, assert_api_stopped, rollback_activation

TABLES = {"plexus_graph": ["edges", "road_costs"], "plexus_atlas": ["atlas_metadata"]}


class FakeStore:
    def __init__(self):
        self.tables = {
            "plexus_graph.edges": "old_edges",
            "plexus_capacity_graph.edges": "new_edges",
            "plexus_capacity_graph.road_costs": "new_costs",
            "plexus_atlas.atlas_metadata": "old_meta",
            "plexus_capacity_atlas.atlas_metadata": "new_meta",
        }
        self.original = dict(self.tables)
        self.commands = []
        self.exchanges = 0
        self.fail_after_exchange = None
        self.crash_after_exchange = None
        self.crash_after_install = False
        self.created = 0

    def rows(self, query):
        if "system.tables" in query:
            database, table = re.search(
                r"database='([^']+)' AND name='([^']+)'", query
            ).groups()
            identifier = self.tables.get(database + "." + table)
            return [{"uuid": identifier}] if identifier else []
        if "plexus_state.road_jobs" in query or "SELECT count()" in query:
            return [{"n": 0}]
        if "key='artifact_version'" in query:
            return [
                {
                    "value": "new_artifact"
                    if self.tables.get("plexus_atlas.atlas_metadata") == "new_meta"
                    else "old_artifact"
                }
            ]
        raise AssertionError(query)

    def execute(self, query):
        self.commands.append(query)
        tokens = query.split()
        if query.startswith("CREATE TABLE IF NOT EXISTS"):
            self.created += 1
            self.tables.setdefault(tokens[5], "empty_" + str(self.created))
        elif query.startswith("RENAME TABLE"):
            self.tables[tokens[4]] = self.tables.pop(tokens[2])
            if self.crash_after_install:
                self.crash_after_install = False
                raise KeyboardInterrupt("Crash after placeholder installation")
        elif query.startswith("EXCHANGE TABLES"):
            left, right = tokens[2], tokens[4]
            self.tables[left], self.tables[right] = (
                self.tables[right],
                self.tables[left],
            )
            self.exchanges += 1
            if self.exchanges == self.fail_after_exchange:
                self.fail_after_exchange = None
                raise RuntimeError("Failure after real exchange")
            if self.exchanges == self.crash_after_exchange:
                self.crash_after_exchange = None
                raise KeyboardInterrupt("Crash before journal completion")
        elif query.startswith("DROP TABLE"):
            self.tables.pop(tokens[2])
        elif not query.startswith("SYSTEM"):
            raise AssertionError(query)


class ApiGateTests(unittest.TestCase):
    def test_only_connection_refused_proves_api_is_stopped(self):
        with patch(
            "road_capacity.activate.socket.create_connection",
            side_effect=ConnectionRefusedError,
        ):
            assert_api_stopped("http://127.0.0.1:8007")
        for error in [TimeoutError("busy socket"), OSError("unreachable")]:
            with (
                patch(
                    "road_capacity.activate.socket.create_connection", side_effect=error
                ),
                self.assertRaisesRegex(ValueError, "Cannot establish"),
            ):
                assert_api_stopped("http://localhost:8007")

    def test_any_running_listener_is_blocked_regardless_of_http_status(self):
        connection = Mock()
        with (
            patch(
                "road_capacity.activate.socket.create_connection",
                return_value=connection,
            ),
            self.assertRaisesRegex(ValueError, "Stop the local API"),
        ):
            assert_api_stopped("http://127.0.0.1:8007")
        connection.close.assert_called_once()

    def test_remote_or_authenticated_url_is_rejected(self):
        for url in [
            "http://example.com:8007",
            "http://user:pass@localhost:8007",
            "ftp://127.0.0.1:8007",
        ]:
            with self.assertRaises(ValueError):
                assert_api_stopped(url)


class JournalRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.root = Path(self.directory.name)
        self.store = FakeStore()
        self.patches = [
            patch("road_capacity.activate.TABLES", TABLES),
            patch("road_capacity.activate.assert_api_stopped"),
            patch(
                "road_capacity.activate.validate",
                return_value={"artifact_version": "new_artifact"},
            ),
        ]
        for item in self.patches:
            item.start()

    def tearDown(self):
        for item in reversed(self.patches):
            item.stop()
        self.directory.cleanup()

    def call(self):
        return activate(self.store, self.root, "http://127.0.0.1:8007")

    def journal(self):
        return json.loads(
            (self.root / "data/road-capacity/activation.json").read_text()
        )

    def test_completed_exchange_has_uuid_plan_and_metadata_is_last(self):
        result = self.call()
        self.assertEqual(result["status"], "completed")
        self.assertEqual(result["plan"][0]["active_uuid"], "old_edges")
        self.assertEqual(result["plan"][1]["active_uuid"], None)
        exchanges = [
            query for query in self.store.commands if query.startswith("EXCHANGE")
        ]
        self.assertIn("plexus_atlas.atlas_metadata", exchanges[-1])
        self.assertEqual(self.store.tables["plexus_graph.road_costs"], "new_costs")
        count = len(self.store.commands)
        self.call()
        self.assertEqual(len(self.store.commands), count)

    def test_exception_after_unrecorded_exchange_uses_uuid_rollback(self):
        self.store.fail_after_exchange = 2
        with self.assertRaisesRegex(RuntimeError, "Failure after"):
            self.call()
        self.assertEqual(self.journal()["status"], "rolled_back")
        self.assertEqual(self.store.tables, self.store.original)

    def test_crash_after_exchange_recovers_before_retry(self):
        self.store.crash_after_exchange = 2
        with self.assertRaises(KeyboardInterrupt):
            self.call()
        self.assertEqual(self.journal()["pending"]["operation"], "exchange")
        result = self.call()
        self.assertEqual(result["status"], "completed")
        self.assertEqual(self.store.tables["plexus_graph.edges"], "new_edges")
        self.assertEqual(self.store.tables["plexus_atlas.atlas_metadata"], "new_meta")

    def test_crash_after_placeholder_rename_recovers(self):
        self.store.crash_after_install = True
        with self.assertRaises(KeyboardInterrupt):
            self.call()
        self.assertEqual(self.journal()["pending"]["operation"], "install_empty")
        self.assertEqual(self.call()["status"], "completed")

    def test_explicit_rollback_restores_absent_new_table(self):
        self.call()
        result = rollback_activation(self.store, self.root, "http://127.0.0.1:8007")
        self.assertEqual(result["status"], "rolled_back")
        self.assertEqual(self.store.tables, self.store.original)
        rollback_activation(self.store, self.root, "http://127.0.0.1:8007")
        self.assertEqual(self.store.tables, self.store.original)

    def test_external_uuid_drift_is_not_treated_as_success(self):
        self.call()
        self.store.tables["plexus_graph.edges"] = "external_uuid"
        with self.assertRaisesRegex(ValueError, "Unexpected table UUID"):
            self.call()
