import os
import sys
import unittest
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from road_traffic.assumptions import POLICY, lane_view_sql
from road_traffic.storage import Storage


class AssumptionSqlTests(unittest.TestCase):
    def test_identifiers_cannot_inject_sql(self):
        for name in ["bad.name", "x;DROP DATABASE data", "", "1db"]:
            with self.assertRaises(ValueError):
                lane_view_sql(name)


@unittest.skipUnless(
    os.environ.get("ROAD_TRAFFIC_INTEGRATION") == "1", "Explicit scratch DB"
)
class LaneAssumptionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        url = os.environ["TRAFFIC_TEST_CLICKHOUSE_URL"]
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
        cls.store = Storage("plexus_lanes_test_" + uuid4().hex)
        cls.store.initialize()
        fixtures = [
            (1, "unknown", "missing", "primary", None, "{}", []),
            (2, "bidirectional", "missing", "primary", None, "{}", []),
            (3, "forward", "missing", "primary", None, "{}", []),
            (4, "reverse", "missing", "primary", None, "{}", []),
            (5, "unknown", "valid", "primary", 4, '{"lanes":"4"}', []),
            (6, "unknown", "invalid", "primary", None, '{"lanes":"bad"}', []),
            (7, "unknown", "missing", "ferry", None, "{}", []),
            (8, "alternating", "missing", "primary", None, "{}", []),
            (9, "reversible", "missing", "primary", None, "{}", []),
            (
                10,
                "unknown",
                "missing",
                "primary",
                None,
                "{bad",
                ["source_tags:invalid"],
            ),
            (
                11,
                "unknown",
                "missing",
                "primary",
                None,
                '{"lanes:conditional":"2 @ wet"}',
                [],
            ),
            (12, "unknown", "contradictory", "primary", 2, "{}", []),
        ]
        cls.store.insert(
            "road_attributes",
            [
                {
                    "run_id": "fixture",
                    "way_id": way,
                    "way_idx": way,
                    "oneway": direction,
                    "lanes_status": status,
                    "highway": highway,
                    "lanes_total": total,
                    "lanes_forward": None,
                    "lanes_backward": None,
                    "lanes_both_ways": None,
                    "source_tags": raw,
                    "quality": quality,
                }
                for way, direction, status, highway, total, raw, quality in fixtures
            ],
        )

    @classmethod
    def tearDownClass(cls):
        try:
            cls.store.execute(f"DROP DATABASE {cls.store.database} SYNC")
        finally:
            cls.environment.stop()

    def rows(self):
        return {
            int(r["way_id"]): r
            for r in self.store.rows(
                f"SELECT * FROM {self.store.database}.road_attributes_effective"
            )
        }

    def test_two_way_fallback_is_one_lane_each_and_missing_source_stays_missing(self):
        for key in [1, 2]:
            row = self.rows()[key]
            self.assertIsNone(row["lanes_total"])
            self.assertEqual(row["lanes_status"], "missing")
            self.assertEqual(row["effective_lanes_total"], 2)
            self.assertEqual(row["effective_lanes_forward"], 1)
            self.assertEqual(row["effective_lanes_backward"], 1)
            self.assertEqual(row["lanes_basis"], POLICY)
        self.assertTrue(self.rows()[1]["bidirectional_assumed"])
        self.assertFalse(self.rows()[2]["bidirectional_assumed"])

    def test_forward_and_reverse_oneway_keep_their_direction(self):
        for key, forward, backward in [(3, 1, 0), (4, 0, 1)]:
            row = self.rows()[key]
            self.assertEqual(row["effective_lanes_total"], 1)
            self.assertEqual(row["effective_lanes_forward"], forward)
            self.assertEqual(row["effective_lanes_backward"], backward)

    def test_known_data_and_unresolved_conflicts_are_not_replaced(self):
        rows = self.rows()
        self.assertEqual(rows[5]["effective_lanes_total"], 4)
        self.assertEqual(rows[5]["lanes_basis"], "osm")
        for key in range(5, 13):
            self.assertFalse(rows[key]["lanes_assumed"])
        self.assertEqual(rows[12]["effective_lanes_total"], 2)
        self.assertEqual(rows[12]["lanes_basis"], "unresolved")

    def test_reinitializing_view_preserves_raw_values_and_does_not_duplicate_rows(self):
        before = self.rows()
        self.store.initialize()
        self.assertEqual(self.rows(), before)
