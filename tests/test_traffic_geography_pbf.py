import sqlite3
import tempfile
import unittest
from pathlib import Path

from shapely.geometry import shape
from synthetic_traffic.geography_pbf import build_vector_cache, query_vector_cache


class GeographyPbfTests(unittest.TestCase):
    def fixture(self, root, incomplete=False):
        nodes = [
            (1, 40, 50),
            (2, 40.01, 50),
            (3, 40.01, 50.01),
            (4, 40, 50.01),
            (5, 40.003, 50.003),
            (6, 40.007, 50.003),
            (7, 40.007, 50.007),
            (8, 40.003, 50.007),
        ]
        content = '<osm version="0.6"><bounds minlat="49" minlon="39" maxlat="51" maxlon="41"/>'
        content += "".join(
            f'<node id="{node}" lon="{lon}" lat="{lat}" version="1"/>'
            for node, lon, lat in nodes
        )
        refs = [1, 2, 3] if incomplete else [1, 2, 3, 4, 1]
        content += (
            '<way id="100" version="1">'
            + "".join(f'<nd ref="{node}"/>' for node in refs)
            + "</way>"
        )
        content += '<way id="101" version="1"><nd ref="5"/><nd ref="6"/><nd ref="7"/><nd ref="8"/><nd ref="5"/></way>'
        content += '<way id="102" version="1"><nd ref="1"/><nd ref="3"/><tag k="waterway" v="river"/></way>'
        content += '<way id="103" version="1"><nd ref="1"/><nd ref="2"/><nd ref="3"/><nd ref="4"/><nd ref="1"/><tag k="leisure" v="nature_reserve"/></way>'
        content += '<relation id="200" version="1"><member type="way" ref="100" role="outer"/><member type="way" ref="101" role="inner"/><tag k="type" v="multipolygon"/><tag k="building" v="yes"/></relation></osm>'
        path = root / "source.osm"
        path.write_text(content)
        return path

    def test_assembled_holes_spatial_queries_and_waterway_resolution(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self.fixture(root)
            cache = root / "vectors.sqlite"
            manifest = build_vector_cache(source, cache)
            self.assertEqual(manifest["status"], "complete")
            self.assertEqual(
                manifest["features"], {"buildings": 1, "water": 1, "protected": 1}
            )
            features = query_vector_cache(cache, [39.99, 49.99, 40.02, 50.02])
            building = shape(features["buildings"][0]["geometry"])
            self.assertAlmostEqual(building.area, 0.0001 - 0.000016)
            self.assertTrue(
                all(
                    not rows
                    for rows in query_vector_cache(
                        cache, [39.1, 49.1, 39.2, 49.2]
                    ).values()
                )
            )
            larger = query_vector_cache(
                cache, [39.99, 49.99, 40.02, 50.02], resolution=0.002
            )
            self.assertGreater(
                shape(larger["water"][0]["geometry"]).area,
                shape(features["water"][0]["geometry"]).area,
            )
            self.assertEqual(
                build_vector_cache(source, cache)["pbf_sha256"], manifest["pbf_sha256"]
            )

    def test_incomplete_area_does_not_publish_a_complete_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self.fixture(root, incomplete=True)
            cache = root / "vectors.sqlite"
            with self.assertRaises((ValueError, RuntimeError)):
                build_vector_cache(source, cache)
            self.assertFalse(cache.exists())
            self.assertFalse(list(root.glob("*.building")))

    def test_reader_rejects_unfinished_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            cache = Path(directory) / "vectors.sqlite"
            with sqlite3.connect(cache) as connection:
                connection.execute("CREATE TABLE metadata (key TEXT,value TEXT)")
                connection.execute(
                    "INSERT INTO metadata VALUES ('manifest','{\"status\":\"building\"}')"
                )
            with self.assertRaisesRegex(ValueError, "incomplete"):
                query_vector_cache(cache, [40, 50, 41, 51])

    def test_exact_coverage_rejects_a_hole_inside_the_header_bounds(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self.fixture(root)
            cache = root / "vectors.sqlite"
            coverage = {
                "type": "Polygon",
                "coordinates": [
                    [[39, 49], [41, 49], [41, 51], [39, 51], [39, 49]],
                    [
                        [40.1, 50.1],
                        [40.2, 50.1],
                        [40.2, 50.2],
                        [40.1, 50.2],
                        [40.1, 50.1],
                    ],
                ],
            }
            manifest = build_vector_cache(source, cache, coverage=coverage)
            self.assertEqual(manifest["coverage_geometry"], coverage)
            with self.assertRaisesRegex(
                ValueError, "vector_cache_coverage_unavailable"
            ):
                query_vector_cache(cache, [40.12, 50.12, 40.18, 50.18])

    def test_missing_member_cache_is_retained_then_repaired_from_complete_source(self):
        from synthetic_traffic.geography_pbf_repair import repair_vector_cache

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self.fixture(root)
            complete_source = root / "200.osm"
            complete_source.write_bytes(source.read_bytes())
            source.write_text(
                source.read_text().replace(
                    'ref="100" role="outer"', 'ref="999" role="outer"'
                )
            )
            cache = root / "vectors.sqlite"
            with self.assertRaisesRegex(ValueError, "assembly incomplete"):
                build_vector_cache(source, cache)
            incomplete = root / "vectors.sqlite.incomplete"
            self.assertTrue(incomplete.exists())
            with self.assertRaisesRegex(ValueError, "incomplete"):
                query_vector_cache(incomplete, [39.99, 49.99, 40.02, 50.02])
            manifest = repair_vector_cache(incomplete, cache, root)
            self.assertEqual(manifest["status"], "complete")
            self.assertEqual(
                manifest["snapshot_basis"],
                "mixed_original_pbf_and_current_official_osm_api",
            )
            self.assertEqual(manifest["repairs"][0]["osm_id"], 200)
            features = query_vector_cache(cache, [39.99, 49.99, 40.02, 50.02])
            self.assertEqual(len(features["buildings"]), 1)

    def test_invalid_source_ring_is_deferred_and_repaired_without_empty_clearance(self):
        from synthetic_traffic.geography_pbf_repair import repair_vector_cache

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self.fixture(root)
            malformed = '<way id="104" version="1"><nd ref="1"/><nd ref="3"/><nd ref="2"/><nd ref="4"/><nd ref="1"/><tag k="building" v="yes"/></way>'
            document = source.read_text().replace(
                '<relation id="200"', malformed + '<relation id="200"'
            )
            source.write_text(document)
            (root / "104.osm").write_text(document)
            cache = root / "vectors.sqlite"
            with self.assertRaisesRegex(ValueError, "assembly incomplete"):
                build_vector_cache(source, cache)
            incomplete = root / "vectors.sqlite.incomplete"
            with sqlite3.connect(incomplete) as db:
                missing = db.execute(
                    "SELECT layer,kind,osm_id FROM expected"
                ).fetchall()
            self.assertEqual(missing, [("buildings", "way", 104)])
            manifest = repair_vector_cache(incomplete, cache, root)
            self.assertEqual(manifest["features"]["buildings"], 2)
            self.assertEqual(
                manifest["repairs"][0]["topology_repair"],
                "make_valid_recorded_closed_ring",
            )
            self.assertTrue(
                query_vector_cache(cache, [39.99, 49.99, 40.02, 50.02])["buildings"]
            )

    def test_closed_water_rings_keep_a_conservative_mask_for_short_stray_member(self):
        from synthetic_traffic.geography_pbf_repair import repaired_geometry

        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = self.fixture(root)
            text = source.read_text().replace(
                '<way id="100"',
                '<node id="9" lon="39.9997" lat="50" version="1"/><way id="100"',
            )
            text = text.replace(
                '<relation id="200"',
                '<way id="105" version="1"><nd ref="1"/><nd ref="9"/></way><relation id="200"',
            )
            text = text.replace(
                '<member type="way" ref="100" role="outer"/>',
                '<member type="way" ref="100" role="outer"/><member type="way" ref="105" role="outer"/>',
            )
            text = text.replace(
                '<tag k="building" v="yes"/>', '<tag k="natural" v="water"/>'
            )
            source.write_text(text)
            geometry, metadata = repaired_geometry(source, "relation", 200)
            self.assertTrue(geometry.is_valid)
            self.assertLess(geometry.bounds[0], 39.9997)
            self.assertEqual(metadata["conservative_member_buffer_degrees"], 0.0005)
            self.assertIn("conservative", metadata["topology_repair"])
