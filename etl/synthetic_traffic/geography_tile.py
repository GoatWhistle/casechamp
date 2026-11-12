import json
import math
from datetime import UTC, datetime
from pathlib import Path
from tempfile import TemporaryDirectory
from uuid import uuid4

import numpy as np
import rasterio
from rasterio.enums import Resampling
from rasterio.transform import from_origin
from rasterio.warp import reproject
from synthetic_traffic.geography import RasterGeography
from synthetic_traffic.geography_prepare import prepare
from synthetic_traffic.geography_tile_sources import _dem, _hash, _vectors


def fetch_tile(bbox, output_dir, cache_dir, resolution=0.001, vector_cache=None):
    west, south, east, north = map(float, bbox)
    if (
        not -180 <= west < east <= 180
        or not -85 <= south < north <= 85
        or not 0.00025 <= resolution <= 0.01
    ):
        raise ValueError(
            "Tile bounds/resolution must be ordered WGS84 within85degrees and0.00025..0.01degrees"
        )
    west = math.floor(west / resolution + 1e-8) * resolution
    south = math.floor(south / resolution + 1e-8) * resolution
    east = math.ceil(east / resolution - 1e-8) * resolution
    north = math.ceil(north / resolution - 1e-8) * resolution
    rows, cols = (
        round((north - south) / resolution) + 1,
        round((east - west) / resolution) + 1,
    )
    if rows * cols > 1_000_000:
        raise ValueError("A geographic tile is limited to one million grid cells")
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    bounds = [west, south, east, north]
    transform = from_origin(
        west - resolution / 2, north + resolution / 2, resolution, resolution
    )
    elevation = np.full((rows, cols), np.nan, dtype=np.float32)
    manifest = {
        "status": "preparing",
        "acquired_at": datetime.now(UTC).isoformat(),
        "bbox": bounds,
        "resolution_degrees": resolution,
        "files": {},
        "limits": [
            "OSM mapped features are not surveyed clearance",
            "GLO30 is a surface model including vegetation and structures",
            "Missing terrain fails acquisition; unmapped vector features can still exist",
        ],
    }
    with TemporaryDirectory(prefix="raw-", dir=output) as name:
        temporary = Path(name)
        features, vector_source = _vectors(bounds, resolution, temporary, vector_cache)
        latitude_origins = range(
            math.floor(south - 1 / 7200), math.floor(north - 1 / 7200) + 1
        )
        manifest["terrain_alignment"] = {
            "method": "node_centered_nearest_reprojection",
            "latitude_source_half_pixel_degrees": 1 / 7200,
            "southern_neighbor": "included_when_grid_nodes_cross_GLO30_pixel_footprint_boundary",
        }
        for lat in latitude_origins:
            for lon in range(math.floor(west), math.floor(east) + 1):
                path, record = _dem(lat, lon, Path(cache_dir) / "dem")
                manifest["files"][record["url"]] = record
                tile = np.full(elevation.shape, np.nan, dtype=np.float32)
                with rasterio.open(path) as source:
                    reproject(
                        source=rasterio.band(source, 1),
                        destination=tile,
                        src_nodata=source.nodata,
                        dst_transform=transform,
                        dst_crs="EPSG:4326",
                        dst_nodata=np.nan,
                        resampling=Resampling.nearest,
                        num_threads=1,
                        warp_mem_limit=64,
                    )
                np.copyto(elevation, tile, where=np.isfinite(tile))
        if not np.isfinite(elevation).all():
            raise ValueError(
                "Terrain coverage contains nodata within the requested tile"
            )
        dem = temporary / "dem.npz"
        np.savez_compressed(
            dem,
            elevation_m=elevation[::-1],
            origin_lon=west,
            origin_lat=south,
            cell_degrees=resolution,
        )
        for layer in ("water", "buildings", "protected"):
            path = temporary / f"{layer}.geojson"
            path.write_text(
                json.dumps({"type": "FeatureCollection", "features": features[layer]})
            )
            manifest[layer + "_features"] = len(features[layer])
        prepared = temporary / "geography.json"
        prepare(
            dem,
            temporary / "water.geojson",
            temporary / "buildings.geojson",
            temporary / "protected.geojson",
            prepared,
        )
        surface = RasterGeography.load(prepared)
        surface.sources = {
            "elevation": {
                "provider": "Copernicus GLO30",
                "kind": "DSM",
                "tiles": list(manifest["files"].values()),
            },
            **{
                key: {
                    **vector_source,
                    "features": len(features[key]),
                    "coverage": "OSM mapped features only",
                }
                for key in features
            },
        }
        surface.save(output / "geography.npz")
    manifest.update(
        {
            "status": "complete",
            "geography_file": "geography.npz",
            "sha256": _hash(output / "geography.npz"),
            "bytes": (output / "geography.npz").stat().st_size,
            "rows": rows,
            "cols": cols,
        }
    )
    path = output / "manifest.json"
    temporary_manifest = path.with_name(path.name + "." + uuid4().hex + ".tmp")
    temporary_manifest.write_text(json.dumps(manifest, indent=2) + "\n")
    temporary_manifest.replace(path)
    return manifest
