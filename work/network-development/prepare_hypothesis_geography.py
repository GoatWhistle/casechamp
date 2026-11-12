import argparse
import hashlib
import json
import math
import sqlite3
import time
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
from rasterio.features import rasterize
from rasterio.transform import from_origin
from shapely import from_wkb, prepare
from shapely.geometry import box, mapping, shape
from synthetic_traffic import geography_tile
from synthetic_traffic.geography import RasterGeography
from synthetic_traffic.geography_fetch import dem_url

ROOT = Path(__file__).resolve().parents[2]
BOUNDS = [41.7, 44.44, 42.2, 44.81]


def digest(path):
    with Path(path).open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def known_vectors(cache, bounds, resolution, provenance):
    coverage = shape(provenance["coverage_geometry"])
    known = coverage.intersection(box(*bounds).buffer(resolution))
    prepare(known)
    west, south, east, north = bounds
    features = {key: [] for key in ("water", "buildings", "protected")}
    with sqlite3.connect(cache.resolve().as_uri() + "?mode=ro", uri=True) as connection:
        rows = connection.execute(
            "SELECT f.layer,f.kind,f.osm_id,f.basis,f.wkb FROM features f JOIN spatial s ON s.id=f.id WHERE s.max_lon>=? AND s.min_lon<=? AND s.max_lat>=? AND s.min_lat<=?",
            (
                west - resolution,
                east + resolution,
                south - resolution,
                north + resolution,
            ),
        )
        for layer, kind, osm_id, basis, encoded in rows:
            geometry = from_wkb(encoded)
            if basis == "waterway_centerline":
                geometry = geometry.buffer(resolution / 2)
            if known.intersects(geometry):
                features[layer].append(
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
    return features


def run(cache, terrain_cache, output, resolution=0.001):
    started = time.monotonic()
    cache, terrain_cache, output = Path(cache), Path(terrain_cache), Path(output)
    for lat in range(math.floor(BOUNDS[1]), math.floor(BOUNDS[3]) + 1):
        for lon in range(math.floor(BOUNDS[0]), math.floor(BOUNDS[2]) + 1):
            name = hashlib.sha256(dem_url(lat, lon).encode()).hexdigest()
            if not (terrain_cache / "dem" / f"{name}.tif").is_file():
                raise ValueError(
                    "Required terrain is not cached; manual preparation will not download missing data"
                )
    with sqlite3.connect(cache.resolve().as_uri() + "?mode=ro", uri=True) as connection:
        provenance = json.loads(
            connection.execute(
                "SELECT value FROM metadata WHERE key='manifest'"
            ).fetchone()[0]
        )
    if provenance.get("status") != "complete" or not provenance.get(
        "coverage_geometry"
    ):
        raise ValueError(
            "Manual preparation requires a completed vector cache with known exact coverage"
        )
    coverage = shape(provenance["coverage_geometry"])
    if not coverage.is_valid:
        raise ValueError("Source coverage is invalid")
    coverage_sha = hashlib.sha256(
        json.dumps(
            provenance["coverage_geometry"], sort_keys=True, separators=(",", ":")
        ).encode()
    ).hexdigest()
    vector_sha = digest(cache)

    def partial_vectors(bounds, requested_resolution, temporary, vector_cache):
        return known_vectors(cache, bounds, requested_resolution, provenance), {
            "provider": "OpenStreetMap PBF vector cache",
            "path": str(cache.resolve()),
            "sha256": vector_sha,
            "source_manifest": provenance,
            "coverage_check": "manual_partial_pilot_uncovered_cells_blocked",
        }

    output.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="preparing-", dir=output) as directory:
        original = geography_tile._vectors
        try:
            geography_tile._vectors = partial_vectors
            manifest = geography_tile.fetch_tile(
                BOUNDS,
                directory,
                terrain_cache,
                resolution=resolution,
                vector_cache=cache,
            )
        finally:
            geography_tile._vectors = original
        surface = RasterGeography.load(Path(directory) / "geography.npz")
    west, south, east, north = manifest["bbox"]
    margin = resolution * 0.001
    unknown = box(west, south, east, north).difference(coverage.buffer(-margin))
    mask = rasterize(
        [(mapping(unknown), 1)],
        out_shape=surface.blocked.shape,
        transform=from_origin(
            west - resolution / 2, north + resolution / 2, resolution, resolution
        ),
        all_touched=True,
        fill=0,
        dtype="uint8",
    )[::-1].astype(bool)
    newly_blocked = int(np.count_nonzero(mask & ~surface.blocked))
    surface.blocked |= mask
    base_unknown = box(*BOUNDS).difference(coverage)
    coverage_record = {
        "status": "partial",
        "reason": "Exact source extract does not cover a western triangle; uncovered cells and an inward margin of 0.001 raster cell are blocked",
        "uncovered_blocked_cells": int(mask.sum()),
        "newly_blocked_cells": newly_blocked,
        "coverage_polygon_sha256": coverage_sha,
        "coverage_inset_degrees": margin,
        "all_touched": True,
        "known_area_fraction": 1 - base_unknown.area / box(*BOUNDS).area,
        "uncovered_area_square_degrees": base_unknown.area,
    }
    surface.sources["coverage"] = coverage_record
    target = output / "geography.npz"
    surface.save(target)
    checked = RasterGeography.load(target)
    if not np.all(checked.blocked[mask]):
        raise ValueError("An uncovered raster cell remained traversable")
    manifest.update(
        status="partial",
        bbox=BOUNDS,
        sha256=digest(target),
        bytes=target.stat().st_size,
        coverage=coverage_record,
        vector_cache_sha256=vector_sha,
        preparation_seconds=time.monotonic() - started,
        comparison_policy="Freeze this exact geography SHA for both pilot arms; this is not full regional coverage",
    )
    temporary_manifest = output / "manifest.json.tmp"
    temporary_manifest.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    temporary_manifest.replace(output / "manifest.json")
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--vector-cache",
        default=ROOT / "data/traffic-geography-national/vector-cache.sqlite",
        type=Path,
    )
    parser.add_argument(
        "--terrain-cache",
        default=ROOT / "data/traffic-geography-national/cache",
        type=Path,
    )
    parser.add_argument(
        "--output", default=ROOT / "data/traffic-geography-hypothesis-pilot", type=Path
    )
    args = parser.parse_args()
    print(
        json.dumps(
            run(args.vector_cache, args.terrain_cache, args.output),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
