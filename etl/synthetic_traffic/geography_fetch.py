import argparse
import hashlib
import json
import math
from datetime import UTC, datetime
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np
from shapely.geometry import mapping
from synthetic_traffic.geography_fetch_osm import osm_geometry
from synthetic_traffic.geography_prepare import prepare

try:
    import rasterio
except ImportError:
    rasterio = None
DEM_BASE = "https://copernicus-dem-30m.s3.amazonaws.com"
OVERPASS = "https://overpass.private.coffee/api/interpreter"


def download(url, destination, body=None, timeout=120):
    request = Request(
        url,
        data=body,
        headers={"User-Agent": "PlexusGeography/1.0 public-data research"},
    )
    with urlopen(request, timeout=timeout) as response:
        declared = response.headers.get("Content-Length")
        expected = int(declared) if declared is not None else None
        if expected is not None and not 0 <= expected <= 100_000_000:
            raise ValueError(
                "Public data response declares an invalid or oversized body"
            )
        payload = response.read(100_000_001)
        if expected is not None and len(payload) != expected:
            raise ValueError(
                f"Incomplete public data response: received {len(payload)} of {expected} declared bytes"
            )
    if len(payload) > 100_000_000:
        raise ValueError("Public data response exceeded the 100 MB safety limit")
    Path(destination).write_bytes(payload)
    return {
        "url": url,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "bytes": len(payload),
    }


def dem_url(lat, lon):
    north = f"{'N' if lat >= 0 else 'S'}{abs(lat):02d}_00"
    east = f"{'E' if lon >= 0 else 'W'}{abs(lon):03d}_00"
    tile = f"Copernicus_DSM_COG_10_{north}_{east}_DEM"
    return f"{DEM_BASE}/{tile}/{tile}.tif"


def fetch(bbox, output, resolution=0.001, endpoint=OVERPASS):
    if rasterio is None:
        raise RuntimeError("Public terrain acquisition requires rasterio")
    west, south, east, north = bbox
    if not -180 <= west < east <= 180 or not -85 <= south < north <= 85:
        raise ValueError("Bounds must be west south east north in WGS84")
    if (east - west) * (north - south) > 0.5 or not 0.00025 <= resolution <= 0.01:
        raise ValueError(
            "Fetch is limited to 0.5 square degrees and resolution 0.00025..0.01"
        )
    rows, cols = (
        math.floor((north - south) / resolution + 1e-9) + 1,
        math.floor((east - west) / resolution + 1e-9) + 1,
    )
    if rows * cols > 1_000_000:
        raise ValueError("Geography raster is limited to one million cells")
    output = Path(output)
    output.mkdir(parents=True, exist_ok=True)
    manifest = {
        "acquired_at": datetime.now(UTC).isoformat(),
        "bbox": bbox,
        "resolution_degrees": resolution,
        "files": {},
        "limits": [
            "OSM completeness is not guaranteed; absence is not surveyed clearance",
            "Waterway lines conservatively occupy one raster cell, not a measured channel width",
            "Copernicus GLO30 is a surface model including vegetation and structures",
            "Prepared raster is for preliminary screening, not construction approval",
        ],
    }
    bounds = f"({south},{west},{north},{east})"
    selectors = (
        "[building]",
        "[natural=water]",
        "[waterway]",
        "[landuse=reservoir]",
        "[boundary=protected_area]",
        "[leisure=nature_reserve]",
    )
    query = (
        "[out:json][timeout:90];("
        + "".join(f"nwr{selector}{bounds};" for selector in selectors)
        + ");out geom;"
    )
    raw = output / "osm.json"
    manifest["files"][raw.name] = download(
        endpoint, raw, urlencode({"data": query}).encode()
    )
    osm = json.loads(raw.read_text())
    if osm.get("remark"):
        raise ValueError(f"Overpass did not complete: {osm['remark']}")
    features = {"water": [], "buildings": [], "protected": []}
    for element in osm.get("elements", []):
        if element["type"] == "node":
            continue
        tags = element.get("tags", {})
        layer = (
            "buildings"
            if "building" in tags
            else "protected"
            if tags.get("boundary") == "protected_area"
            or tags.get("leisure") == "nature_reserve"
            else "water"
        )
        geometry = osm_geometry(element, resolution)
        features[layer].append(
            {
                "type": "Feature",
                "geometry": mapping(geometry),
                "properties": {
                    "osm_type": element["type"],
                    "osm_id": element["id"],
                    "tags": tags,
                },
            }
        )
    for layer, values in features.items():
        path = output / f"{layer}.geojson"
        path.write_text(json.dumps({"type": "FeatureCollection", "features": values}))
        manifest[f"{layer}_features"] = len(values)
    coordinates = [
        (west + col * resolution, south + row * resolution)
        for row in range(rows)
        for col in range(cols)
    ]
    elevations = np.full((rows, cols), np.nan)
    grouped = {}
    for index, (lon, lat) in enumerate(coordinates):
        grouped.setdefault((math.floor(lat), math.floor(lon)), []).append(index)
    for (lat, lon), indices in grouped.items():
        url = dem_url(lat, lon)
        tile = output / url.split("/")[-1]
        manifest["files"][tile.name] = download(url, tile)
        with rasterio.open(tile) as dataset:
            samples = list(
                dataset.sample([coordinates[index] for index in indices], masked=True)
            )
            for index, sample in zip(indices, samples, strict=True):
                if np.ma.is_masked(sample[0]):
                    raise ValueError(
                        "Terrain tile has missing elevations inside requested bounds"
                    )
                elevations.flat[index] = sample[0]
    if not np.isfinite(elevations).all():
        raise ValueError("Incomplete terrain surface")
    dem = output / "dem.npz"
    np.savez_compressed(
        dem,
        elevation_m=elevations,
        origin_lon=west,
        origin_lat=south,
        cell_degrees=resolution,
    )
    raster_path = output / "geography.json"
    prepare(
        dem,
        output / "water.geojson",
        output / "buildings.geojson",
        output / "protected.geojson",
        raster_path,
    )
    payload = json.loads(raster_path.read_text())
    payload["sources"] = {
        "elevation": {
            "provider": DEM_BASE,
            "tiles": [name for name in manifest["files"] if name.endswith(".tif")],
            "kind": "DSM",
        },
        **{
            key: {
                "provider": "OpenStreetMap via Overpass",
                "endpoint": endpoint,
                "acquired_at": manifest["acquired_at"],
                "features": len(features[key]),
                "coverage": "OSM mapped features only",
            }
            for key in features
        },
    }
    raster_path.write_text(json.dumps(payload))
    (output / "manifest.json").write_text(json.dumps(manifest, indent=2))
    return manifest


def main():
    parser = argparse.ArgumentParser(description="Fetch public corridor geography")
    parser.add_argument(
        "--bbox",
        nargs=4,
        type=float,
        required=True,
        metavar=("WEST", "SOUTH", "EAST", "NORTH"),
    )
    parser.add_argument("--output", required=True)
    parser.add_argument("--resolution", type=float, default=0.001)
    parser.add_argument("--overpass", default=OVERPASS)
    args = parser.parse_args()
    result = fetch(args.bbox, args.output, args.resolution, args.overpass)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
