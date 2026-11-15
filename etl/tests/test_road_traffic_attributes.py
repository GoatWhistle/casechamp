import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from road_traffic.attributes import normalize_way


class RoadTrafficAttributesTests(unittest.TestCase):
    def way(self, **tags):
        return normalize_way(
            {
                "way_id": 123,
                "way_idx": 5,
                "highway": "primary",
                "km": 2.5,
                "source_tags": json.dumps(tags),
            }
        )

    def test_missing_lanes_and_direction_are_not_inferred_from_road_class(self):
        row = self.way()
        self.assertIsNone(row["lanes_total"])
        self.assertIsNone(row["lanes_forward"])
        self.assertEqual(row["lanes_status"], "missing")
        self.assertEqual(row["oneway"], "unknown")
        self.assertEqual(row["way_id"], 123)
        self.assertEqual(row["km"], 2.5)

    def test_odd_lane_total_does_not_infer_directional_split(self):
        row = self.way(lanes="3", oneway="no")
        self.assertEqual(row["lanes_total"], 3)
        self.assertIsNone(row["lanes_forward"])
        self.assertIsNone(row["lanes_backward"])
        self.assertEqual(row["lanes_status"], "valid")

    def test_shared_turn_lane_is_not_added_to_either_direction(self):
        row = self.way(
            **{
                "lanes": "3",
                "lanes:forward": "1",
                "lanes:backward": "1",
                "lanes:both_ways": "1",
            }
        )
        self.assertEqual(row["lanes_forward"], 1)
        self.assertEqual(row["lanes_backward"], 1)
        self.assertEqual(row["lanes_both_ways"], 1)
        self.assertEqual(row["lanes_status"], "valid")

    def test_directional_sum_over_total_is_contradictory(self):
        row = self.way(**{"lanes": "2", "lanes:forward": "2", "lanes:backward": "2"})
        self.assertEqual(row["lanes_status"], "contradictory")
        self.assertEqual(row["lanes_total"], 2)
        self.assertIn("lanes:directional_sum_conflict", row["quality"])

    def test_reverse_direction_is_preserved(self):
        row = self.way(oneway="-1", lanes="2")
        self.assertEqual(row["oneway"], "reverse")
        self.assertIsNone(row["lanes_backward"])
        self.assertEqual(row["raw_tags"]["oneway"], "-1")

    def test_explicit_bidirectional_overrides_roundabout(self):
        self.assertEqual(self.way(junction="roundabout")["direction_status"], "implied")
        self.assertEqual(
            self.way(junction="roundabout", oneway="no")["oneway"], "bidirectional"
        )

    def test_contradictory_oneway_lanes_are_flagged_without_discarding_values(self):
        row = self.way(**{"oneway": "yes", "lanes:backward": "1"})
        self.assertEqual(row["lanes_status"], "contradictory")
        self.assertEqual(row["lanes_backward"], 1)

    def test_bus_lane_stays_in_total_and_restrictions_stay_raw(self):
        row = self.way(**{"lanes": "3", "lanes:bus": "1"})
        self.assertEqual(row["lanes_total"], 3)
        self.assertEqual(row["raw_tags"]["lanes:bus"], "1")

    def test_ambiguous_lanes_are_not_cast_to_a_single_value(self):
        row = self.way(lanes="2;3")
        self.assertIsNone(row["lanes_total"])
        self.assertEqual(row["lanes_status"], "ambiguous")

    def test_invalid_lane_counts_are_not_filled(self):
        for value in ["-2", "2.5", "unknown", "0"]:
            row = self.way(lanes=value)
            self.assertIsNone(row["lanes_total"])
            self.assertEqual(row["lanes_status"], "invalid")

    def test_mph_conversion_and_directional_speeds(self):
        row = self.way(
            **{
                "maxspeed": "60 mph",
                "maxspeed:forward": "90",
                "maxspeed:backward": "70 km/h",
            }
        )
        self.assertAlmostEqual(row["maxspeed_kmh"], 96.56064)
        self.assertEqual(row["maxspeed_forward_kmh"], 90)
        self.assertEqual(row["maxspeed_backward_kmh"], 70)

    def test_symbolic_speed_keeps_unknown_numeric_limit(self):
        for value in ["none", "walk", "RU:rural", "signals", "50;70"]:
            row = self.way(maxspeed=value)
            self.assertIsNone(row["maxspeed_kmh"])
            self.assertEqual(row["maxspeed_status"], "ambiguous")

    def test_conditional_restriction_is_not_applied_as_permanent(self):
        row = self.way(
            **{"lanes": "3", "lanes:bus:conditional": "1 @ (Mo-Fr 07:00-19:00)"}
        )
        self.assertEqual(row["lanes_total"], 3)
        self.assertIn("conditional_attributes_present", row["quality"])

    def test_bad_source_json_is_retained_and_flagged(self):
        row = normalize_way({"way_id": 1, "source_tags": "{bad"})
        self.assertEqual(row["source_tags"], "{bad")
        self.assertIn("source_tags:invalid", row["quality"])
        self.assertIsNone(row["lanes_total"])


if __name__ == "__main__":
    unittest.main()
