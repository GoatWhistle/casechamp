import os
import sys
import unittest
from pathlib import Path

import pyarrow as pa

ROOT = Path(__file__).resolve().parents[2]
MAIN = Path(os.environ.get("ROAD_CAPACITY_SOURCE_ROOT", ROOT))
sys.path[:0] = [str(ROOT / "etl"), str(MAIN / "etl"), str(MAIN / "backend/src")]

from road_capacity.weights import profile, profile_schema


class ProfileBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.road = {
            "way_id": 1,
            "way_idx": 0,
            "highway": "primary",
            "km": 10.0,
            "source_speed_kmh": 60.0,
            "lanes_status": "missing",
        }

    def test_missing_lanes_are_one_representative_direction_not_observed(self):
        result = profile(self.road)
        self.assertEqual(result["effective_speed_kmh"], 60.0)
        self.assertEqual(result["capacity_pcu_h"], 1800.0)
        self.assertEqual(result["lane_basis"], "narrow_unknown_lanes_v1")
        self.assertEqual(result["flow_basis"], "unknown_free_flow")
        self.assertFalse(result["flow_verified"])
        self.assertIsNone(result["hourly_flow_pcu"])

    def test_invalid_lanes_preserve_raw_counts_without_fabricating_capacity(self):
        result = profile(
            {
                **self.road,
                "lanes_status": "contradictory",
                "lanes_total": 2,
                "lanes_forward": 3,
            }
        )
        self.assertEqual(result["lanes_total"], 2)
        self.assertEqual(result["lanes_forward"], 3)
        self.assertFalse(result["lane_data_usable"])
        self.assertIsNone(result["capacity_pcu_h"])
        self.assertEqual(result["effective_speed_kmh"], 60.0)

    def test_tag_valid_but_unsplittable_lanes_are_explicitly_unresolved(self):
        result = profile(
            {
                **self.road,
                "lanes_status": "valid",
                "lanes_total": 2,
                "lanes_forward": 2,
                "oneway": "unknown",
            }
        )
        self.assertFalse(result["lane_data_usable"])
        self.assertEqual(result["lanes_forward"], 2)
        self.assertIsNone(result["capacity_pcu_h"])
        self.assertEqual(result["effective_speed_kmh"], 60.0)

    def test_ferry_capacity_stays_null(self):
        result = profile(
            {
                **self.road,
                "highway": "ferry",
                "is_ferry": True,
                "source_speed_kmh": 10.0,
            }
        )
        self.assertIsNone(result["capacity_pcu_h"])
        self.assertEqual(result["flow_basis"], "not_applicable")
        self.assertEqual(result["effective_speed_kmh"], 10.0)
        values = pa.Table.from_pylist([result], schema=profile_schema())
        self.assertIsNone(values["capacity_pcu_h"][0].as_py())

    def test_posted_speed_is_ceiling_after_surface_adjustment(self):
        result = profile({**self.road, "surface": "gravel", "posted_speed_kmh": 30.0})
        self.assertEqual(result["effective_speed_kmh"], 30.0)

    def test_prohibited_direction_zero_is_preserved(self):
        result = profile(
            {
                **self.road,
                "lanes_status": "valid",
                "oneway": "forward",
                "lanes_total": 2,
                "lanes_forward": 2,
                "lanes_backward": 0,
            }
        )
        self.assertEqual(result["lanes_backward"], 0)
        self.assertEqual(result["capacity_pcu_h"], 3600.0)

    def test_reversible_and_unresolved_central_lanes_have_no_capacity(self):
        for extras in [
            {"oneway": "reversible"},
            {"lanes_total": 3, "lanes_both_ways": 1},
        ]:
            result = profile({**self.road, **extras})
            self.assertFalse(result["lane_data_usable"])
            self.assertIsNone(result["capacity_pcu_h"])


if __name__ == "__main__":
    unittest.main()
