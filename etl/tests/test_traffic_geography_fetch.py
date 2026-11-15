import unittest

from synthetic_traffic.geography_fetch import dem_url, osm_geometry


class GeographyFetchTests(unittest.TestCase):
    def test_copernicus_uses_signed_tile_origin(self):
        self.assertIn("_N44_00_E041_00_DEM", dem_url(44, 41))
        self.assertIn("_S01_00_W001_00_DEM", dem_url(-1, -1))

    def test_relation_assembles_fragmented_ring_and_hole(self):
        def member(coordinates, role):
            return {
                "type": "way",
                "role": role,
                "geometry": [{"lon": lon, "lat": lat} for lon, lat in coordinates],
            }

        geometry = osm_geometry(
            {
                "type": "relation",
                "id": 1,
                "members": [
                    member([(0, 0), (4, 0), (4, 4)], "outer"),
                    member([(4, 4), (0, 4), (0, 0)], "outer"),
                    member([(1, 1), (2, 1), (2, 2), (1, 2), (1, 1)], "inner"),
                ],
            },
            0.001,
        )
        self.assertAlmostEqual(geometry.area, 15)

    def test_incomplete_area_fails_instead_of_silently_disappearing(self):
        with self.assertRaises(ValueError):
            osm_geometry(
                {
                    "type": "way",
                    "id": 1,
                    "geometry": [{"lon": 0, "lat": 0}, {"lon": 1, "lat": 1}],
                },
                0.001,
            )
