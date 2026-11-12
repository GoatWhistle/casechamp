import json
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "etl"))
from synthetic_traffic.assignment import assign, costs
from synthetic_traffic.demand import aggregate, generate
from synthetic_traffic.housing import distribute
from synthetic_traffic.model import DemandParameters, Network, Trip, Zone
from synthetic_traffic.projects import apply_project
from synthetic_traffic.report import compare


def network(
    source=(0, 0, 1, 2),
    target=(1, 2, 3, 3),
    free=(1.0, 1.2, 1.0, 1.2),
    capacity=(100.0, 100.0, 100.0, 100.0),
):
    size = max(*source, *target) + 1
    count = len(source)
    return Network(
        np.array(source),
        np.array(target),
        np.array(free),
        np.array(capacity),
        np.ones(count),
        np.arange(count),
        np.arange(size),
        np.zeros(size),
        np.arange(size, dtype=float) * 0.001,
        np.full(count, -1),
    )


class SyntheticTrafficTests(unittest.TestCase):
    def test_joint_demand_adds_on_shared_edges(self):
        graph = network((0, 1, 2), (1, 2, 3), (1.0, 1.0, 1.0), (1000.0, 1000.0, 1000.0))
        result = assign(graph, [Trip(0, 3, 100), Trip(1, 3, 50)])
        np.testing.assert_allclose(result.flow, [100, 150, 150])
        self.assertTrue(result.converged)

    def test_parallel_roads_are_not_summed_into_one_edge(self):
        graph = network((0, 0), (1, 1), (1.0, 1.1), (100.0, 100.0))
        result = assign(graph, [Trip(0, 1, 200)], iterations=2000, tolerance=0.002)
        self.assertTrue(result.converged)
        self.assertGreater(min(result.flow), 0)
        self.assertAlmostEqual(result.flow.sum(), 200)

    def test_direction_and_unserved_flow_are_preserved(self):
        graph = network((0,), (1,), (1.0,), (100.0,))
        result = assign(graph, [Trip(1, 0, 80)])
        self.assertEqual(result.unserved_vehicles_per_hour, 80)
        self.assertIsNone(result.od_hours[0])
        self.assertEqual(result.flow.sum(), 0)

    def test_shared_single_lane_uses_combined_directional_demand(self):
        graph = network((0, 1), (1, 0), (1.0, 1.0), (100.0, 100.0))
        graph.shared[:] = 0
        result = assign(graph, [Trip(0, 1, 70), Trip(1, 0, 60)])
        np.testing.assert_allclose(result.ratio, [1.3, 1.3])

    def test_capacity_expansion_keeps_demand_and_reduces_delay(self):
        graph = network((0,), (1,), (1.0,), (1800.0,))
        before = assign(graph, [Trip(0, 1, 2000)])
        changed = apply_project(graph, {"kind": "capacity", "way_ids": [0]})
        after = assign(changed, [Trip(0, 1, 2000)])
        self.assertEqual(after.flow[0], before.flow[0])
        self.assertLess(after.hours[0], before.hours[0])
        self.assertEqual(graph.capacity[0], 1800)

    def test_local_project_rejects_transcontinental_shortcut(self):
        graph = network()
        graph.lon[-1] = 150
        with self.assertRaises(ValueError):
            apply_project(
                graph,
                {
                    "kind": "connection",
                    "source_node": 0,
                    "target_node": 3,
                    "length_km": 5,
                },
            )

    def test_missing_and_oversized_projects_fail(self):
        graph = network()
        with self.assertRaises(ValueError):
            apply_project(graph, {"kind": "speed", "way_ids": [999]})
        with self.assertRaises(ValueError):
            apply_project(
                replace(graph, length_km=np.full(4, 31.0)),
                {"kind": "speed", "way_ids": [0]},
            )

    def test_generation_and_zoning_preserve_population(self):
        graph = network((0, 1, 1, 2), (1, 0, 2, 1))
        zones = [
            Zone("a", 0, 1000, 0, 0),
            Zone("b", 1, 2000, 0, 0.001),
            Zone("c", 2, 3000, 0, 0.002),
        ]
        grouped, _ = aggregate(zones, graph, 0.01, 3)
        self.assertEqual(sum(z.population for z in grouped), 6000)
        parameters = DemandParameters()
        trips, info = generate(graph, zones, parameters)
        self.assertAlmostEqual(
            sum(t.vehicles_per_hour for t in trips), parameters.production(6000)
        )
        self.assertEqual(info["unavailable_destination_vehicles_per_hour"], 0)

    def test_disconnected_origins_keep_unavailable_demand(self):
        graph = network((0,), (1,), (1.0,), (100.0,))
        _, info = generate(
            graph,
            [Zone("a", 1, 1000, 0, 0.001), Zone("b", 0, 2000, 0, 0)],
            DemandParameters(),
        )
        self.assertGreater(info["unavailable_destination_vehicles_per_hour"], 0)

    def test_housing_weights_allocate_known_population_without_multiplication(self):
        graph = network()
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "homes.parquet"
            pq.write_table(
                pa.table(
                    {
                        "id": ["small", "large"],
                        "lat": [0.0, 0.0],
                        "lon": [0.0, 0.001],
                        "residential_m2_proxy": [100.0, 300.0],
                    }
                ),
                path,
            )
            zones, info = distribute(path, [Zone("a", 0, 400, 0, 0)], graph)
            np.testing.assert_allclose([z.population for z in zones], [100, 300])
            self.assertEqual(info["allocated_population"], 400)

    def test_fixed_demand_checksum_and_relief_report(self):
        graph = network((0,), (1,), (1.0,), (1800.0,))
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "result"
            result = compare(
                graph,
                [Trip(0, 1, 2000)],
                [{"kind": "capacity", "way_ids": [0]}],
                path,
                1.0,
                100,
                0.001,
                {},
                [0.7, 1.0, 1.3],
            )
            self.assertEqual(len(result["cases"]), 3)
            self.assertGreater(
                result["cases"][1]["projects"][0]["vehicle_hours_saved"], 0
            )
            saved = json.loads((path / "demand.json").read_text())
            self.assertEqual(saved[0]["vehicles_per_hour"], 2000)

    def test_new_local_connection_takes_flow_without_creating_demand(self):
        graph = network((0, 1), (1, 2), (1.0, 1.0), (100.0, 100.0))
        project = {
            "kind": "connection",
            "source_node": 0,
            "target_node": 2,
            "length_km": 0.25,
            "speed_kmh": 40,
        }
        result = assign(apply_project(graph, project), [Trip(0, 2, 200)])
        self.assertAlmostEqual(result.flow[-2], 200)
        self.assertAlmostEqual(result.flow[0], 0)
        self.assertEqual(result.unserved_vehicles_per_hour, 0)

    def test_assignment_conserves_flow_at_junctions(self):
        graph = network()
        result = assign(graph, [Trip(0, 3, 250)])
        balance = np.bincount(graph.source, weights=result.flow, minlength=4)
        balance -= np.bincount(graph.target, weights=result.flow, minlength=4)
        np.testing.assert_allclose(balance, [250, 0, 0, -250], atol=1e-9)

    def test_unconverged_results_do_not_claim_saved_vehicle_hours(self):
        with tempfile.TemporaryDirectory() as temporary:
            result = compare(
                network(),
                [Trip(0, 3, 500)],
                [{"kind": "speed", "way_ids": [0], "factor": 1.2}],
                Path(temporary) / "result",
                1.0,
                1,
                1e-12,
                {},
                [1.0],
            )
            self.assertFalse(result["cases"][0]["baseline"]["converged"])
            self.assertIsNone(result["cases"][0]["projects"][0]["vehicle_hours_saved"])

    def test_new_access_is_not_reported_as_negative_time_saving(self):
        graph = network((0, 2), (1, 3), (1.0, 1.0), (1800.0, 1800.0))
        project = {
            "kind": "connection",
            "source_node": 1,
            "target_node": 2,
            "length_km": 0.15,
            "speed_kmh": 40,
        }
        with tempfile.TemporaryDirectory() as temporary:
            report = compare(
                graph,
                [Trip(0, 3, 100)],
                [project],
                Path(temporary) / "result",
                1.0,
                100,
                0.001,
                {},
                [1.0],
            )
            result = report["cases"][0]["projects"][0]
            self.assertEqual(result["unserved_vehicles_reduction"], 100)
            self.assertIsNone(result["vehicle_hours_saved"])

    def test_invalid_demand_and_network_are_rejected(self):
        with self.assertRaises(ValueError):
            DemandParameters(car_share=2)
        with self.assertRaises(ValueError):
            assign(network(), [Trip(0, 1, float("nan"))])
        with self.assertRaises(ValueError):
            costs(network(), np.array([float("inf")] * 4))


if __name__ == "__main__":
    unittest.main()
