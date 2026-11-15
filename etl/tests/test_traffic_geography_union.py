import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from shapely.geometry import box, mapping, shape
from synthetic_traffic.geography_pbf_storage import query_vector_cache
from synthetic_traffic.geography_pbf_union import merge_vector_caches


def fixture(path, geometry, timestamp, coverage, basis="assembled_osm_area"):
    with sqlite3.connect(path) as db:
        db.executescript(
            "CREATE TABLE features(id INTEGER PRIMARY KEY,layer TEXT,kind TEXT,osm_id INTEGER,basis TEXT,wkb BLOB);CREATE VIRTUAL TABLE spatial USING rtree(id,min_lon,max_lon,min_lat,max_lat);CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT);"
        )
        db.execute(
            "INSERT INTO features VALUES(1,'buildings','way',100,?,?)",
            (basis, geometry.wkb),
        )
        west, south, east, north = geometry.bounds
        db.execute("INSERT INTO spatial VALUES(1,?,?,?,?)", (west, east, south, north))
        db.execute(
            "INSERT INTO metadata VALUES('manifest',?)",
            (
                json.dumps(
                    {
                        "status": "complete",
                        "osm_timestamp": timestamp,
                        "coverage_geometry": mapping(coverage),
                    }
                ),
            ),
        )


class GeographyUnionTests(unittest.TestCase):
    def setUp(self):
        space = patch('synthetic_traffic.geography_pbf_union.shutil.disk_usage',
                      return_value=SimpleNamespace(free=100 * 1024**3))
        space.start()
        self.addCleanup(space.stop)

    def test_newer_source_updates_geometry_and_rtree_and_union_covers_both(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            north, south, merged = (
                root / "north.sqlite",
                root / "south.sqlite",
                root / "union.sqlite",
            )
            fixture(north, box(40, 50, 40.01, 50.01), "2026-11-07", box(39, 49, 41, 51))
            fixture(
                south, box(41.2, 50, 41.21, 50.01), "2026-11-11", box(41, 49, 42, 51)
            )
            manifest = merge_vector_caches([south, north], merged)
            self.assertEqual(manifest["features"], {"buildings": 1})
            self.assertTrue(
                shape(manifest["coverage_geometry"]).covers(box(40.5, 49.5, 41.5, 50.5))
            )
            self.assertFalse(
                query_vector_cache(merged, [39.99, 49.99, 40.02, 50.02])["buildings"]
            )
            self.assertEqual(
                len(
                    query_vector_cache(merged, [41.19, 49.99, 41.22, 50.02])[
                        "buildings"
                    ]
                ),
                1,
            )
            with sqlite3.connect(merged) as db:
                self.assertEqual(
                    db.execute("SELECT source_cache FROM features").fetchone()[0], 1
                )

    def test_current_official_repair_wins_over_a_newer_raw_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            north, south, merged = (
                root / "north.sqlite",
                root / "south.sqlite",
                root / "union.sqlite",
            )
            coverage = box(39, 49, 42, 51)
            fixture(
                north,
                box(40, 50, 40.01, 50.01),
                "2026-11-07",
                coverage,
                "official_osm_api_complete_area_repair",
            )
            fixture(south, box(41.2, 50, 41.21, 50.01), "2026-11-11", coverage)
            merge_vector_caches([north, south], merged)
            self.assertEqual(
                len(
                    query_vector_cache(merged, [39.99, 49.99, 40.02, 50.02])[
                        "buildings"
                    ]
                ),
                1,
            )
            self.assertFalse(
                query_vector_cache(merged, [41.19, 49.99, 41.22, 50.02])["buildings"]
            )


def test_union_refuses_insufficient_disk_before_creating_output(tmp_path):
    north, south, output = (tmp_path / name for name in ('north.sqlite', 'south.sqlite', 'union.sqlite'))
    coverage = box(39, 49, 42, 51)
    fixture(north, box(40, 50, 40.01, 50.01), '2026-11-07', coverage)
    fixture(south, box(41.2, 50, 41.21, 50.01), '2026-11-11', coverage)
    with patch('synthetic_traffic.geography_pbf_union.shutil.disk_usage',
               return_value=SimpleNamespace(free=1024)), unittest.TestCase().assertRaises(RuntimeError):
        merge_vector_caches([north, south], output)
    assert not output.exists()
