import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pandas as pd
from scipy.sparse.csgraph import dijkstra

sys.path[:0] = [str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parents[2] / 'backend/src')]
from accessibility.network import best_times, ferry_edges, local_matrix
from accessibility.report import regional_values
from graphlib import build_csr


class PotentialNetworkTests(unittest.TestCase):
    def test_disconnected_population_stays_in_regional_denominator(self):
        source = SimpleNamespace(
            cities=pd.DataFrame({'population': [1000.]}),
            points=pd.DataFrame({'population': [10., 90.], 'region': ['R', 'R']}),
            regions=pd.DataFrame({'region_id': ['01'], 'region': ['R']}),
            normalization=100.,
        )
        rows = regional_values(source, np.array([[2.], [np.inf]]))
        self.assertEqual(rows[('01', 2)], (50., .1, 100))

    def test_ferry_boarding_is_charged_once_per_way_in_both_directions(self):
        edges = pd.DataFrame({'src': [0, 1, 1, 2], 'dst': [1, 0, 2, 1],
                              'h': [.2, .2, .3, .3], 'way_idx': [0, 0, 0, 0]})
        ways = pd.DataFrame({'way_idx': [0], 'is_ferry': [True]})
        src, dst, hours, count = ferry_edges(edges, ways, 4, False)
        graph = build_csr(np.concatenate(src).astype(int), np.concatenate(dst).astype(int), np.concatenate(hours), count)
        distances = dijkstra(graph, directed=True, indices=[0, 2])
        self.assertAlmostEqual(distances[0, 2], 1.)
        self.assertAlmostEqual(distances[1, 0], 1.)
        self.assertTrue(np.isinf(distances[0, 3]))
        src, dst, hours, count = ferry_edges(edges, ways, 4, True)
        self.assertEqual(sum(map(len, src)), 0)

    def test_local_air_uses_travel_without_wait_and_removal_disconnects_origin(self):
        edges = pd.DataFrame({'src': [0, 1], 'dst': [1, 0], 'h': [2., 2.], 'way_idx': [0, 0]})
        ways = pd.DataFrame({'way_idx': [0], 'is_ferry': [False]})
        source = SimpleNamespace(
            points=pd.DataFrame({'point_id': ['a', 'b', 'c'], 'node': [0, 1, -1], 'snap_h': [0., 0., 0.]}),
            cities=pd.DataFrame({'city': ['A', 'B'], 'node': [0, 1], 'snap_h': [0., 0.]}),
            manual=pd.DataFrame({'season': ['summer'], 'from_id': ['c'], 'to_id': ['a'], 'mode': ['air'], 'travel_h': [1.]}),
            trunk=pd.DataFrame(columns=['city_from', 'city_to', 'transport_type', 'distance_hr']),
            graph=lambda: (edges, ways))
        roads, cities = local_matrix(source, 'summer', 'full', 1)
        full = best_times(source, roads, cities)
        np.testing.assert_allclose(full[2], [1., 3.])
        roads, cities = local_matrix(source, 'summer', 'air', 1)
        self.assertTrue(np.isinf(best_times(source, roads, cities, 'air')[2]).all())

    def test_trunk_is_directed_and_retains_terminal_overhead(self):
        source = SimpleNamespace(cities=pd.DataFrame({'city': ['A', 'B']}),
            trunk=pd.DataFrame({'city_from': ['A'], 'city_to': ['B'], 'transport_type': ['air'], 'distance_hr': [1.]}))
        road = np.array([[0., 10.], [10., 0.]])
        best = best_times(source, road, road)
        self.assertEqual(best[0, 1], 3.5)
        self.assertEqual(best[1, 0], 10.)
        np.testing.assert_array_equal(best_times(source, road, road, 'air'), road)


if __name__ == '__main__':
    unittest.main()
