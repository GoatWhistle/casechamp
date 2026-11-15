import os
import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
MAIN = Path(os.environ.get("ROAD_CAPACITY_SOURCE_ROOT", ROOT))
sys.path[:0] = [str(ROOT / "etl"), str(MAIN / "etl"), str(MAIN / "backend/src")]

from app.adapter.road_graph.data import GraphData
from app.adapter.road_graph.routing import GraphRouting
from road_capacity.network import network, road_matrix


class TinySnapshot:
    revision = "capacity-test-legacy"

    def arrays(self, name):
        return {
            "edges": {
                "src": np.array([0, 1]),
                "dst": np.array([1, 2]),
                "h": np.array([1.0, 1.0]),
                "km": np.array([60.0, 60.0]),
                "way_idx": np.array([0, 1]),
            },
            "nodes": {"lat": np.zeros(3), "lon": np.arange(3)},
            "ranks": {"rank": np.array([2, 2])},
        }[name]

    def read(self, query, parameters=None):
        return {
            "model_version": [],
            "road_cost_model": [],
            "points": [("a", 0, 0.0), ("b", 1, 0.0), ("c", 2, 0.0)],
            "origins": [("a", 100), ("b", 200), ("c", 300)],
            "cities": [("A", 0, 0.0, 100000, "a"), ("B", 2, 0.0, 200000, "c")],
            "trunk": [("A", "B", "rail", 0.1)],
            "manual": [("a", "c", 0.5, "bus")],
            "normalization": [(100000.0,)],
        }[query]


class SharedKernelTests(unittest.TestCase):
    def test_runtime_and_etl_road_rows_agree_under_legacy_trunk_policy(self):
        with tempfile.TemporaryDirectory() as directory:
            routing = GraphRouting(GraphData(Path(directory), TinySnapshot()))
            captured = {}
            index, *_ = routing.calculate(
                "r",
                "road",
                [],
                lambda value: None,
                on_times=lambda ids, markets, times: captured.update(best=times),
            )
            graph, lookup = network(routing, "road")
            roads = road_matrix(routing, "road", lookup, ["a", "b", "c"])
            np.testing.assert_allclose(roads, [[0.0, 2.0], [1.0, 1.0], [2.0, 0.0]])
            self.assertAlmostEqual(graph[0, 1], graph[1, 0])
            self.assertAlmostEqual(captured["best"][0, 1], 1.1, places=6)
            population = np.array([100.0, 200.0, 300.0])
            access = np.exp(-np.log(2) / 2 * captured["best"]) @ np.array(
                [100000.0, 200000.0]
            )
            expected = access @ population / population.sum() / 100000 * 100
            self.assertAlmostEqual(index, expected, places=7)

    def test_seasonal_manual_connection_is_in_identical_local_network(self):
        with tempfile.TemporaryDirectory() as directory:
            routing = GraphRouting(GraphData(Path(directory), TinySnapshot()))
            routing.calculate("r", "summer", [], lambda value: None)
            graph, lookup = network(routing, "summer")
            roads = road_matrix(routing, "summer", lookup, ["a", "b", "c"])
            self.assertAlmostEqual(graph[0, 2], 0.5)
            np.testing.assert_allclose(roads, [[0.0, 0.5], [1.0, 1.0], [0.5, 0.0]])


if __name__ == "__main__":
    unittest.main()
