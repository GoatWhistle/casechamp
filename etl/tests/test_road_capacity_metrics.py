import os
import sys
import unittest
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix

ROOT = Path(__file__).resolve().parents[2]
MAIN = Path(os.environ.get("ROAD_CAPACITY_SOURCE_ROOT", ROOT))
sys.path[:0] = [str(ROOT / "etl"), str(MAIN / "etl"), str(MAIN / "backend/src")]

from road_capacity.metrics import network_efficiency, point_metrics
from road_capacity.network import local_times


class PointMetricTests(unittest.TestCase):
    def setUp(self):
        self.origins = pd.DataFrame(
            {
                "point_id": ["a", "b"],
                "population": [1, 3],
                "lat": [0.0, 1.0],
                "lon": [0.0, 0.0],
                "rai_2km": [True, False],
            }
        )
        self.cities = [("A", 0, 0.0, 100000, "a"), ("B", 1, 0.0, 500000, "b")]
        self.times = np.array([[0.0, 2.0], [2.0, 0.0]])
        self.local = {
            "t_district_center_h": np.array([0.0, 0.5]),
            "t_centre_1k_h": np.array([0.0, 0.25]),
            "t_centre_5k_h": np.array([0.0, 0.5]),
            "t_centre_18k_h": np.array([0.0, 1.0]),
        }
        self.reference = {
            "normalization_base": 100000.0,
            "ca_log_min": np.log(400000.0),
            "ca_log_max": np.log(1040000.0),
            "aria_means": {k: 1.0 for k in "abcde"},
        }

    def test_all_market_metrics_use_new_times_and_fixed_normalization(self):
        result = point_metrics(
            self.origins,
            self.times,
            self.times,
            self.cities,
            self.local,
            self.reference,
        )
        np.testing.assert_allclose(result.hansen_2h, [350000.0, 550000.0])
        np.testing.assert_allclose(result.hansen_idx, [350.0, 550.0])
        np.testing.assert_allclose(result.harris, [400000.0, 1040000.0])
        np.testing.assert_allclose(result.remoteness_ca, [1.0, 0.0])
        np.testing.assert_allclose(result.cum_pop_1h, [100000.0, 500000.0])
        np.testing.assert_allclose(result.cum_pop_2h, [600000.0, 600000.0])
        self.assertEqual(result.rai_2km.tolist(), [True, False])
        self.assertAlmostEqual(
            np.average(result.hansen_idx, weights=result.population), 500.0
        )

    def test_no_route_has_zero_access_and_unknown_times(self):
        empty = np.full((2, 2), np.inf)
        result = point_metrics(
            self.origins, empty, empty, self.cities, self.local, self.reference
        )
        self.assertTrue((result.hansen_idx == 0).all())
        self.assertTrue((result.remoteness_ca == 1).all())
        self.assertTrue(result.t_city50k_best_h.isna().all())
        self.assertTrue(result.oecd_remote.all())

    def test_aria_and_lancet_use_updated_local_centres(self):
        before = point_metrics(
            self.origins,
            self.times,
            self.times,
            self.cities,
            self.local,
            self.reference,
        )
        local = {key: np.array([3.0, 3.0]) for key in self.local}
        after = point_metrics(
            self.origins, self.times, self.times, self.cities, local, self.reference
        )
        self.assertTrue((after.aria > before.aria).all())
        self.assertTrue(before.lancet_2h.all())
        self.assertFalse(after.lancet_2h.any())

    def test_network_efficiency_uses_finite_routes_and_geodesic_distance(self):
        coordinates = np.array([[0.0, 0.0], [1.0, 0.0]])
        weights = np.array([100000.0, 500000.0])
        actual = network_efficiency(self.times, self.origins, coordinates, weights)
        expected = 2 / (12742 * np.arcsin(np.sin(np.radians(0.5))) / 90)
        np.testing.assert_allclose(actual, [expected, expected])


class LocalCentreTests(unittest.TestCase):
    def test_local_access_is_recomputed_from_same_undirected_graph(self):
        graph = csr_matrix(
            np.array([[0.0, 0.5, 0.0], [0.5, 0.0, 0.5], [0.0, 0.5, 0.0]])
        )
        origins = pd.DataFrame(
            {
                "point_id": ["a", "b", "c"],
                "population": [20000, 200, 100],
                "is_dc": [True, False, False],
                "region": ["r"] * 3,
                "mun_upper": ["m"] * 3,
            }
        )
        lookup = {"a": [0, 0.0], "b": [1, 0.1], "c": [2, 0.2]}
        result = local_times(graph, lookup, origins)
        np.testing.assert_allclose(result["t_centre_18k_h"], [0.0, 0.6, 1.2])
        np.testing.assert_allclose(result["t_district_center_h"], [0.0, 0.6, 1.2])
        self.assertTrue(result["dc_is_own"].all())
        changed = graph * 2
        after = local_times(changed, lookup, origins)
        np.testing.assert_allclose(after["t_district_center_h"], [0.0, 1.1, 2.2])


if __name__ == "__main__":
    unittest.main()
