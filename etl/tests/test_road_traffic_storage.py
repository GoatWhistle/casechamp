import json
import os
import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

SOURCE_ROOT = Path(
    os.environ.get("ROAD_TRAFFIC_SOURCE_ROOT", Path(__file__).resolve().parents[2])
)
sys.path.insert(0, str(SOURCE_ROOT / "etl"))

from road_traffic.snapshot import snapshot
from road_traffic.storage import TABLES, Storage


@unittest.skipUnless(
    os.environ.get("ROAD_TRAFFIC_INTEGRATION") == "1",
    "Explicit scratch ClickHouse integration run",
)
class StorageIntegrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        url = os.environ.get("TRAFFIC_TEST_CLICKHOUSE_URL")
        if not url:
            raise RuntimeError("TRAFFIC_TEST_CLICKHOUSE_URL is required")
        cls.environment = patch.dict(
            os.environ,
            {
                "CLICKHOUSE_URL": url,
                "CLICKHOUSE_USER": os.environ.get(
                    "TRAFFIC_TEST_CLICKHOUSE_USER", "default"
                ),
                "CLICKHOUSE_PASSWORD": os.environ.get(
                    "TRAFFIC_TEST_CLICKHOUSE_PASSWORD", ""
                ),
            },
        )
        cls.environment.start()
        cls.store = Storage("plexus_traffic_test_" + uuid4().hex)
        cls.store.initialize()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.store.execute(f"DROP DATABASE {cls.store.database} SYNC")
        finally:
            cls.environment.stop()

    def setUp(self):
        for name in TABLES:
            self.store.execute(f"TRUNCATE TABLE {self.store.database}.{name}")

    def test_arrow_round_trip_preserves_nulls_and_arrays(self):
        row = {
            "run_id": "run1",
            "way_id": 9007199254740993,
            "way_idx": 42,
            "highway": "primary",
            "lanes_total": None,
            "lanes_forward": 1,
            "lanes_backward": None,
            "lanes_both_ways": None,
            "lanes_status": "ambiguous",
            "oneway": "no",
            "maxspeed_kmh": None,
            "maxspeed_forward_kmh": 60.0,
            "maxspeed_backward_kmh": None,
            "direction_status": "explicit",
            "maxspeed_status": "valid",
            "source_tags": '{"name":"Дорога \\"тест\\""}',
            "quality": ["missing_total"],
        }
        self.store.insert("road_attributes", [row])
        actual = self.store.rows(
            f"SELECT * FROM {self.store.database}.road_attributes"
        )[0]
        for field in ["way_id", "way_idx"]:
            actual[field] = int(actual[field])
        self.assertEqual(actual, row)
        batches = list(
            self.store.batches(f"SELECT * FROM {self.store.database}.road_attributes")
        )
        self.assertEqual(batches[0].to_pylist(), [row])

    def test_run_latest_status_retains_failed_and_partial_history(self):
        start = datetime(2026, 1, 1)
        for index, status in enumerate(["running", "failed", "partial", "completed"]):
            self.store.insert(
                "runs",
                [
                    {
                        "run_id": "run1",
                        "updated": start + timedelta(seconds=index),
                        "status": status,
                        "record": json.dumps({"stages": {"n": index}}),
                    }
                ],
            )
        actual = self.store.rows(
            f"SELECT status,record FROM {self.store.database}.runs FINAL"
        )
        self.assertEqual(len(actual), 1)
        self.assertEqual(actual[0]["status"], "completed")
        self.assertEqual(json.loads(actual[0]["record"])["stages"]["n"], 3)

    def test_clear_then_repeat_stage_is_idempotent_and_preserves_other_runs(self):
        for run_id, amount in [("run1", 1), ("run2", None)]:
            self.store.insert(
                "traffic_observations",
                [
                    {
                        "run_id": run_id,
                        "observation_id": "obs1",
                        "source_id": "source",
                        "region_id": "r1",
                        "value": amount,
                        "unit": "vehicles/day",
                        "period": "unknown",
                        "record": "{}",
                    }
                ],
            )
        self.store.clear("traffic_observations", "run1")
        self.store.insert(
            "traffic_observations",
            [
                {
                    "run_id": "run1",
                    "observation_id": "obs1",
                    "source_id": "source",
                    "region_id": "r1",
                    "value": 2,
                    "unit": "vehicles/day",
                    "period": "unknown",
                    "record": "{}",
                }
            ],
        )
        actual = self.store.rows(
            f"SELECT run_id,value FROM {self.store.database}.traffic_observations ORDER BY run_id"
        )
        self.assertEqual(
            actual, [{"run_id": "run1", "value": 2}, {"run_id": "run2", "value": None}]
        )

    def test_initialize_repeatedly_preserves_existing_records(self):
        self.store.insert(
            "sources", [{"run_id": "run1", "source_id": "s1", "record": "{}"}]
        )
        self.store.initialize()
        actual = self.store.rows(f"SELECT count() n FROM {self.store.database}.sources")
        self.assertEqual(int(actual[0]["n"]), 1)

    def test_interrupted_snapshot_attachment_recovers_without_duplicate_rows(self):
        store = self.store
        fixture = store.database
        for name in ["ways", "road_lines", "regions", "boundaries"]:
            store.execute(
                f"CREATE TABLE {fixture}.{name}_source (value Int64) ENGINE=MergeTree ORDER BY value"
            )
            store.execute(f"INSERT INTO {fixture}.{name}_source VALUES (1),(2)")

        class SnapshotStore:
            interrupted = False

            def translate(self, sql):
                for source, target in [
                    ("plexus_refresh_graph.ways", "ways"),
                    ("plexus_refresh_graph.road_lines", "road_lines"),
                    ("plexus_atlas.atlas_regions", "regions"),
                    ("plexus_atlas.atlas_boundaries", "boundaries"),
                ]:
                    sql = sql.replace(source, fixture + "." + target + "_source")
                return sql

            def execute(self, sql):
                if "RENAME TABLE" in sql and not self.interrupted:
                    self.interrupted = True
                    raise RuntimeError(
                        "Injected interruption after partition attachment"
                    )
                return store.execute(self.translate(sql))

            def rows(self, sql):
                return store.rows(self.translate(sql))

        run_id = uuid4().hex
        database = "plexus_traffic_snapshot_" + run_id
        proxy = SnapshotStore()
        try:
            with self.assertRaisesRegex(RuntimeError, "Injected interruption"):
                snapshot(proxy, run_id)
            self.assertEqual(snapshot(proxy, run_id), database)
            self.assertEqual(snapshot(proxy, run_id), database)
            for table in ["ways", "road_lines", "regions", "boundaries"]:
                result = store.rows(f"SELECT count() n FROM {database}.{table}")
                self.assertEqual(int(result[0]["n"]), 2)
        finally:
            store.execute(f"DROP DATABASE IF EXISTS {database} SYNC")


if __name__ == "__main__":
    unittest.main()
