import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

SOURCE_ROOT = Path(
    os.environ.get("ROAD_TRAFFIC_SOURCE_ROOT", Path(__file__).resolve().parents[1])
)
sys.path.insert(0, str(SOURCE_ROOT / "etl"))

from road_traffic.inputs import refresh_inputs
from road_traffic.reports import report
from road_traffic.storage import Storage


class ObservationInputTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.code = self.root / "code"
        self.code.mkdir()
        for name in [
            "observations.py",
            "sources.py",
            "new_surveys.py",
            "matching.py",
            "candidates.py",
        ]:
            (self.code / name).write_text("initial code: " + name)
        self.registry = self.root / "datasets/additional/road-traffic"
        self.registry.mkdir(parents=True)
        self.confirmations = self.registry / "confirmations.json"
        self.confirmations.write_text("[]")
        self.surveys = self.root / "data/additional/traffic-surveys"
        self.surveys.mkdir(parents=True)
        self.survey = self.surveys / "observed.csv"
        self.survey.write_text("site,count\none,0\n")
        self.file_patch = patch(
            "road_traffic.inputs.__file__", str(self.code / "inputs.py")
        )
        self.file_patch.start()
        self.state = {"stages": {"attributes": 2, "coverage": {"lines": 2}}}
        refresh_inputs(self.root, self.state)
        self.state["stages"]["observations"] = {"observations": 1}
        self.state["report"] = {"regions": 82}

    def tearDown(self):
        self.file_patch.stop()
        self.temporary.cleanup()

    def assert_observations_invalidated(self):
        refresh_inputs(self.root, self.state)
        self.assertNotIn("observations", self.state["stages"])
        self.assertNotIn("report", self.state)
        self.assertEqual(
            self.state["stages"], {"attributes": 2, "coverage": {"lines": 2}}
        )

    def test_unchanged_inputs_preserve_finished_stages(self):
        digest = self.state["observation_input_digest"]
        refresh_inputs(self.root, self.state)
        self.assertEqual(self.state["observation_input_digest"], digest)
        self.assertEqual(self.state["stages"]["observations"], {"observations": 1})
        self.assertEqual(self.state["report"], {"regions": 82})

    def test_source_code_change_invalidates_observations_only(self):
        (self.code / "sources.py").write_text("new extraction rules")
        self.assert_observations_invalidated()

    def test_confirmation_change_invalidates_observations_only(self):
        self.confirmations.write_text(
            '[{"observation_id":"one","way_id":1,"evidence":"p.2"}]'
        )
        self.assert_observations_invalidated()

    def test_new_source_registry_invalidates_observations_only(self):
        (self.registry / "new-surveys.json").write_text('[{"source_id":"new"}]')
        self.assert_observations_invalidated()

    def test_survey_change_invalidates_observations_only(self):
        self.survey.write_text("site,count\none,1\n")
        self.assert_observations_invalidated()

    def test_failed_run_error_is_cleared_before_retry(self):
        self.state["error"] = "temporary download failure"
        refresh_inputs(self.root, self.state)
        self.assertNotIn("error", self.state)
        self.assertIn("observations", self.state["stages"])


@unittest.skipUnless(
    os.environ.get("ROAD_TRAFFIC_INTEGRATION") == "1",
    "Explicit scratch ClickHouse integration run",
)
class ReportIntegrationTests(unittest.TestCase):
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
        cls.store = Storage("plexus_traffic_report_test_" + uuid4().hex)
        cls.store.initialize()

    @classmethod
    def tearDownClass(cls):
        try:
            cls.store.execute(f"DROP DATABASE {cls.store.database} SYNC")
        finally:
            cls.environment.stop()

    def test_report_has_all_regions_and_distinguishes_zero_missing_and_no_measurement(
        self,
    ):
        store = self.store
        store.execute(
            f"CREATE TABLE {store.database}.regions (id String,name String) ENGINE=MergeTree ORDER BY id"
        )
        store.execute(
            f"INSERT INTO {store.database}.regions SELECT concat('r',leftPad(toString(number),3,'0')),concat('Регион ',toString(number)) FROM numbers(82)"
        )
        store.insert(
            "coverage_parts",
            [
                {
                    "run_id": "test",
                    "region_id": "r000",
                    "way_id": 1,
                    "km": 2.0,
                    "highway": "primary",
                    "lanes_status": "valid",
                    "has_lanes": 1,
                },
                {
                    "run_id": "test",
                    "region_id": "r001",
                    "way_id": 2,
                    "km": 3.0,
                    "highway": "residential",
                    "lanes_status": "missing",
                    "has_lanes": 0,
                },
            ],
        )
        store.insert(
            "traffic_observations",
            [
                {
                    "run_id": "test",
                    "region_id": "r000",
                    "observation_id": "zero",
                    "source_id": "source",
                    "value": 0.0,
                    "unit": "vehicles/hour",
                    "period": "2024",
                    "record": '{"site":"first"}',
                },
                {
                    "run_id": "test",
                    "region_id": "r000",
                    "observation_id": "missing",
                    "source_id": "source",
                    "value": None,
                    "unit": "vehicles/hour",
                    "period": "unknown",
                    "record": '{"site":"second"}',
                },
            ],
        )
        store.insert(
            "graph_matches",
            [
                {
                    "run_id": "test",
                    "observation_id": "zero",
                    "status": "confirmed",
                    "record": "{}",
                }
            ],
        )
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            summary = report(store, "test", store.database, root, root)
            result = json.loads((root / "regional-coverage.json").read_text())
            self.assertEqual(
                summary, {"regions": 82, "observations": 2, "confirmed_observations": 1}
            )
            self.assertEqual(len(result["regions"]), 82)
            first, second, absent = result["regions"][:3]
            self.assertEqual((first["numeric_values"], first["missing_values"]), (1, 1))
            self.assertEqual(first["all_valid_length_share"], 1)
            self.assertEqual(first["confirmed_observations"], 1)
            self.assertEqual(second["all_valid_length_share"], 0)
            self.assertEqual(
                (
                    second["observations"],
                    second["numeric_values"],
                    second["missing_values"],
                ),
                (0, 0, 0),
            )
            self.assertIsNone(absent["all_valid_length_share"])
            raw = store.rows(
                f"SELECT observation_id,value FROM {store.database}.traffic_observations ORDER BY observation_id"
            )
            self.assertEqual(
                raw,
                [
                    {"observation_id": "missing", "value": None},
                    {"observation_id": "zero", "value": 0},
                ],
            )
            self.assertEqual(
                int(
                    store.rows(
                        f"SELECT count() n FROM {store.database}.regional_coverage"
                    )[0]["n"]
                ),
                82,
            )
            report(store, "test", store.database, root, root)
            self.assertEqual(
                int(
                    store.rows(
                        f"SELECT count() n FROM {store.database}.regional_coverage"
                    )[0]["n"]
                ),
                82,
            )
