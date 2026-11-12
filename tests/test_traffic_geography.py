import time
import unittest

import numpy as np
from synthetic_traffic.corridor import find_corridor
from synthetic_traffic.geography import RasterGeography, polyline_km
from synthetic_traffic.projects import connection_design


class GeographyTests(unittest.TestCase):
    def surface(self, **changes):
        values = {
            "origin_lon": 40,
            "origin_lat": 50,
            "cell_degrees": 0.001,
            "elevation_m": np.zeros((9, 9)),
            "blocked": np.zeros((9, 9), dtype=bool),
            "water": np.zeros((9, 9), dtype=bool),
            "sources": {
                key: "test fixture"
                for key in ("elevation", "water", "buildings", "protected")
            },
        }
        values.update(changes)
        return RasterGeography(**values)

    def test_obstacle_requires_nonstraight_alignment(self):
        blocked = np.zeros((9, 9), dtype=bool)
        blocked[1:8, 4] = True
        surface = self.surface(blocked=blocked)
        result = find_corridor(
            surface, surface.coordinate((4, 0)), surface.coordinate((4, 8))
        )
        self.assertIsNotNone(result)
        coordinates = result["geometry"]["coordinates"]
        self.assertGreater(
            result["length_km"], polyline_km([coordinates[0], coordinates[-1]])
        )
        self.assertTrue(all(not blocked[surface.cell(*point)] for point in coordinates))

    def test_impassable_protected_strip_and_deadline(self):
        blocked = np.zeros((9, 9), dtype=bool)
        blocked[:, 4] = True
        surface = self.surface(blocked=blocked)
        self.assertIsNone(
            find_corridor(
                surface, surface.coordinate((4, 0)), surface.coordinate((4, 8))
            )
        )
        surface = self.surface()
        self.assertIsNone(
            find_corridor(
                surface,
                surface.coordinate((4, 0)),
                surface.coordinate((4, 8)),
                time.monotonic() - 1,
            )
        )

    def test_water_and_grade_annotate_structures(self):
        water = np.zeros((9, 9), dtype=bool)
        water[:, 4] = True
        surface = self.surface(water=water)
        result = find_corridor(
            surface, surface.coordinate((4, 0)), surface.coordinate((4, 8))
        )
        self.assertIn("bridge", [item["kind"] for item in result["structures"]])
        elevations = np.zeros((9, 9))
        elevations[:, 4:] = 1000
        surface = self.surface(elevation_m=elevations)
        result = find_corridor(
            surface, surface.coordinate((4, 0)), surface.coordinate((4, 8))
        )
        self.assertIn("tunnel", [item["kind"] for item in result["structures"]])

    def test_new_road_speed_comes_from_provisional_design_and_alignment(self):
        surface = self.surface()
        straight = {
            "geometry": {
                "type": "LineString",
                "coordinates": [surface.coordinate((2, 2)), surface.coordinate((2, 6))],
            },
            "structures": [],
        }
        design = connection_design(straight, surface)
        self.assertEqual(design["road_class"], "two_lane_connector")
        self.assertEqual(design["lanes_per_direction"], 1)
        self.assertEqual(design["surface"], "asphalt")
        self.assertEqual(design["speed_kmh"], 60)
        bent = {
            "geometry": {
                "type": "LineString",
                "coordinates": [
                    surface.coordinate((2, 2)),
                    surface.coordinate((2, 4)),
                    surface.coordinate((4, 4)),
                ],
            }
        }
        self.assertEqual(connection_design(bent, surface)["speed_kmh"], 60)
        bridge = {
            **straight,
            "structures": [
                {"kind": "bridge", "coordinate": surface.coordinate((2, 4))}
            ],
        }
        bridged = connection_design(bridge, surface)
        self.assertLess(bridged["speed_kmh"], 60)
        self.assertGreater(bridged["speed_kmh"], 40)
        surface.elevation_m[2, 6] = 3
        graded = connection_design(straight, surface)
        self.assertLess(graded["speed_kmh"], 60)
        self.assertIn("provisional", graded["speed_basis"]["review"])

    def test_missing_provenance_rejected(self):
        with self.assertRaises(ValueError):
            self.surface(sources={})

    def test_long_polyline_and_package_use_actual_length(self):
        from synthetic_traffic.model import Network
        from synthetic_traffic.projects import apply_project

        graph = Network(
            source=np.array([0, 1]),
            target=np.array([1, 0]),
            free_hours=np.array([1.0, 1.0]),
            capacity=np.array([1800.0, 1800.0]),
            length_km=np.array([100.0, 100.0]),
            way_id=np.array([1, 1]),
            raw_nodes=np.array([10, 20]),
            lat=np.array([50.0, 50.0]),
            lon=np.array([40.0, 41.0]),
            shared=np.array([-1, -1]),
        )
        coordinates = [[40.0, 50.0], [40.5, 50.1], [41.0, 50.0]]
        length = polyline_km(coordinates)
        project = {
            "kind": "connection",
            "source_node": 10,
            "target_node": 20,
            "length_km": length,
            "speed_kmh": 110,
            "capacity_vph": 3600,
            "geometry": {"type": "LineString", "coordinates": coordinates},
        }
        result = apply_project(
            graph,
            {
                "kind": "package",
                "projects": [
                    project,
                    {"kind": "capacity", "way_ids": [1], "extra_lanes": 1},
                ],
            },
        )
        self.assertAlmostEqual(result.free_hours[-1], length / 110)
        self.assertEqual(result.capacity[-1], 3600)
        with self.assertRaises(ValueError):
            apply_project(graph, {**project, "length_km": length / 2})
        with self.assertRaises(ValueError):
            apply_project(graph, {**project, "kind": "opening"})
