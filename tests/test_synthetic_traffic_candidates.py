import sys
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "etl"))
from synthetic_traffic.assignment import assign
from synthetic_traffic.candidates import generate_candidates
from synthetic_traffic.demand import generate
from synthetic_traffic.geography import RasterGeography
from synthetic_traffic.model import DemandParameters, Trip, Zone
from synthetic_traffic.projects import apply_project
from test_synthetic_traffic import network


class SyntheticCandidateTests(unittest.TestCase):
    def test_no_demand_does_not_propose_speculative_projects(self):
        graph = network()
        result = generate_candidates(graph, np.zeros(4), graph.free_hours, np.zeros(4))
        self.assertEqual(result["existing_corridor_projects"], [])
        self.assertEqual(result["connections_for_review"], [])

    def test_existing_projects_obey_shared_physical_limits(self):
        graph = network()
        assigned = assign(graph, [Trip(0, 3, 500)])
        result = generate_candidates(
            graph, assigned.flow, assigned.hours, assigned.ratio, 2
        )
        self.assertTrue(result["existing_corridor_projects"])
        self.assertNotIn(
            "speed", [p["kind"] for p in result["existing_corridor_projects"]]
        )
        self.assertNotIn(
            "capacity", [p["kind"] for p in result["existing_corridor_projects"]]
        )
        self.assertEqual(result["capacity_screening"]["status"], "missing_geography")
        for project in result["existing_corridor_projects"]:
            apply_project(graph, project)
        long = replace(graph, length_km=np.full(4, 31.0))
        result = generate_candidates(
            long, assigned.flow, assigned.hours, assigned.ratio, 2
        )
        self.assertTrue(result["existing_corridor_projects"])
        self.assertNotIn(
            "speed", [p["kind"] for p in result["existing_corridor_projects"]]
        )
        self.assertNotIn(
            "capacity", [p["kind"] for p in result["existing_corridor_projects"]]
        )
        self.assertEqual(result["capacity_screening"]["status"], "missing_geography")

    def test_new_connections_require_geography_evidence(self):
        graph = network(
            (0, 1, 1, 2, 2, 3, 3, 0), (1, 0, 2, 1, 3, 2, 0, 3), (1.0,) * 8, (100.0,) * 8
        )
        assigned = assign(graph, [Trip(0, 2, 500)])
        result = generate_candidates(
            graph, assigned.flow, assigned.hours, assigned.ratio, 2
        )
        self.assertEqual(result["connections_for_review"], [])
        self.assertEqual(result["geography_status"], "unavailable")

    def test_missing_geography_does_not_turn_source_gaps_into_roads(self):
        graph = network()
        assigned = assign(graph, [Trip(0, 3, 500)])
        result = generate_candidates(
            graph, assigned.flow, assigned.hours, assigned.ratio, 2
        )
        self.assertEqual(result["connections_for_review"], [])
        self.assertEqual(result["geography_status"], "unavailable")

    def test_capacity_candidates_require_clear_sourced_raster_footprints(self):
        graph = network()
        graph.lat[:] = 0.002
        graph.lon += 0.002
        assigned = assign(graph, [Trip(0, 3, 500)])
        surface = RasterGeography(
            0,
            0,
            0.001,
            np.zeros((9, 9)),
            np.zeros((9, 9), dtype=bool),
            np.zeros((9, 9), dtype=bool),
            {
                key: "test fixture"
                for key in ("elevation", "water", "buildings", "protected")
            },
        )
        result = generate_candidates(
            graph, assigned.flow, assigned.hours, assigned.ratio, 1, surface
        )
        capacities = [
            p for p in result["existing_corridor_projects"] if p["kind"] == "capacity"
        ]
        self.assertTrue(capacities)
        self.assertTrue(
            all(p["feasibility_status"] == "raster_screened" for p in capacities)
        )
        surface.blocked[:] = True
        blocked = generate_candidates(
            graph, assigned.flow, assigned.hours, assigned.ratio, 1, surface
        )
        self.assertNotIn(
            "capacity", [p["kind"] for p in blocked["existing_corridor_projects"]]
        )
        self.assertGreater(blocked["capacity_screening"]["rejected"], 0)

    def test_trip_profile_does_not_force_daily_demand_to_faraway_destinations(self):
        graph = network((0, 1), (1, 0), (10.0, 10.0), (1800.0, 1800.0))
        trips, info = generate(
            graph,
            [Zone("a", 0, 1000, 0, 0), Zone("b", 1, 1000, 0, 0.001)],
            DemandParameters(),
        )
        self.assertEqual(trips, [])
        self.assertGreater(info["unavailable_destination_vehicles_per_hour"], 0)

    def test_bad_candidate_inputs_fail_clearly(self):
        graph = network()
        with self.assertRaises(ValueError):
            generate_candidates(graph, np.zeros(1), graph.free_hours, np.zeros(4))


if __name__ == "__main__":
    unittest.main()
