import sys
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "etl"))
from synthetic_traffic.assignment import assign
from synthetic_traffic.candidates import generate_candidates
from synthetic_traffic.demand import generate
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
        for project in result["existing_corridor_projects"]:
            apply_project(graph, project)
        long = replace(graph, length_km=np.full(4, 31.0))
        result = generate_candidates(
            long, assigned.flow, assigned.hours, assigned.ratio, 2
        )
        self.assertEqual(result["existing_corridor_projects"], [])

    def test_new_connections_are_bounded_and_flagged_for_engineering_review(self):
        graph = network(
            (0, 1, 1, 2, 2, 3, 3, 0), (1, 0, 2, 1, 3, 2, 0, 3), (1.0,) * 8, (100.0,) * 8
        )
        assigned = assign(graph, [Trip(0, 2, 500)])
        result = generate_candidates(
            graph, assigned.flow, assigned.hours, assigned.ratio, 2
        )
        self.assertTrue(result["connections_for_review"])
        self.assertLessEqual(len(result["connections_for_review"]), 2)
        for project in result["connections_for_review"]:
            self.assertLessEqual(project["length_km"], 5)
            self.assertIn("unverified", project["review"])
            apply_project(graph, project)

    def test_possible_source_gaps_are_kept_out_of_connection_recommendations(self):
        graph = network()
        assigned = assign(graph, [Trip(0, 3, 500)])
        result = generate_candidates(
            graph, assigned.flow, assigned.hours, assigned.ratio, 2
        )
        self.assertEqual(result["connections_for_review"], [])
        self.assertTrue(result["data_gaps"])
        self.assertIn("source_gap", result["data_gaps"][0]["review"])

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
