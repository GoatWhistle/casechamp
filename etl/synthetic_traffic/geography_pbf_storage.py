import json
import sqlite3
from pathlib import Path

from shapely import from_wkb
from shapely.geometry import box, mapping, shape


def read_manifest(connection):
    row = connection.execute(
        "SELECT value FROM metadata WHERE key='manifest'"
    ).fetchone()
    if not row:
        raise ValueError("Vector cache has no completed manifest")
    manifest = json.loads(row[0])
    if manifest.get("status") != "complete":
        raise ValueError("Vector cache is incomplete")
    return manifest


def query_vector_cache(sqlitepath, bbox, resolution=0.001):
    west, south, east, north = map(float, bbox)
    if (
        not -180 <= west < east <= 180
        or not -90 <= south < north <= 90
        or not 0 < resolution <= 0.01
    ):
        raise ValueError(
            "Query requires an ordered WGS84 bbox and positive raster resolution"
        )
    area = box(west, south, east, north)
    result = {key: [] for key in ("buildings", "water", "protected")}
    with sqlite3.connect(f"file:{Path(sqlitepath)}?mode=ro", uri=True) as connection:
        manifest = read_manifest(connection)
        coverage = manifest.get("coverage_geometry")
        if coverage is not None and not shape(coverage).covers(area):
            raise ValueError(
                "vector_cache_coverage_unavailable: query extends beyond the sourced PBF coverage polygon"
            )
        rows = connection.execute(
            "SELECT f.layer,f.kind,f.osm_id,f.basis,f.wkb FROM features f JOIN spatial s ON s.id=f.id WHERE s.max_lon>=? AND s.min_lon<=? AND s.max_lat>=? AND s.min_lat<=?",
            (
                west - resolution / 2,
                east + resolution / 2,
                south - resolution / 2,
                north + resolution / 2,
            ),
        )
        for layer, kind, osm_id, basis, encoded in rows:
            geometry = from_wkb(encoded)
            if basis == "waterway_centerline":
                geometry = geometry.buffer(resolution / 2)
            if not geometry.intersects(area):
                continue
            result[layer].append(
                {
                    "type": "Feature",
                    "geometry": mapping(geometry),
                    "properties": {
                        "osm_type": kind,
                        "osm_id": osm_id,
                        "geometry_basis": basis,
                    },
                }
            )
    return result
