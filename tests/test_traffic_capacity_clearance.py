import unittest

import numpy as np
from synthetic_traffic.capacity_clearance import screen_capacity
from synthetic_traffic.geography import RasterGeography
from synthetic_traffic.model import Network


class CapacityClearanceTests(unittest.TestCase):
    def setUp(self):
        self.surface = RasterGeography(
            40,
            50,
            0.001,
            np.zeros((12, 12)),
            np.zeros((12, 12), dtype=bool),
            np.zeros((12, 12), dtype=bool),
            {
                key: "fixture"
                for key in ("water", "buildings", "protected", "elevation")
            },
        )
        self.network = Network(
            source=np.array([0, 1]),
            target=np.array([1, 0]),
            free_hours=np.array([0.01, 0.01]),
            capacity=np.array([1800.0, 1800.0]),
            length_km=np.array([0.5, 0.5]),
            way_id=np.array([1, 1]),
            raw_nodes=np.array([10, 20]),
            lat=np.array([50.005, 50.005]),
            lon=np.array([40.002, 40.009]),
            shared=np.array([-1, -1]),
        )
        self.project = {"kind": "capacity", "way_ids": [1], "extra_lanes": 1}

    def test_clear_existing_segments_have_sourced_screening_metadata(self):
        result = screen_capacity(self.network, self.project, self.surface)
        self.assertTrue(result["housing_clearance"])
        self.assertEqual(result["widening_buffer_m"], 7)
        self.assertIn("survey", result["review"])

    def test_buildings_protected_water_and_missing_surface_reject(self):
        self.assertIsNone(screen_capacity(self.network, self.project, None))
        for layer in (self.surface.blocked, self.surface.water):
            layer[5, 6] = True
            self.assertIsNone(screen_capacity(self.network, self.project, self.surface))
            layer[5, 6] = False
        self.network.lon[0] = 39.99
        self.assertIsNone(screen_capacity(self.network, self.project, self.surface))

    def test_structure_and_steep_terrain_require_engineering(self):
        self.assertIsNone(
            screen_capacity(
                self.network,
                {**self.project, "structures": [{"kind": "bridge"}]},
                self.surface,
            )
        )
        self.surface.elevation_m[:, 6:] = 100
        self.assertIsNone(screen_capacity(self.network, self.project, self.surface))

    def test_stored_full_polyline_is_screened_instead_of_endpoint_chord(self):
        self.network.geometries = {
            1: [[40.002, 50.005], [40.006, 50.008], [40.009, 50.005]]
        }
        self.surface.blocked[8, 6] = True
        self.assertIsNone(screen_capacity(self.network, self.project, self.surface))
