import argparse
import json
from pathlib import Path

import numpy as np
from rasterio.features import rasterize
from rasterio.transform import from_origin
from shapely.geometry import shape
from synthetic_traffic.geography import RasterGeography


def prepare(dem_path, water_path, buildings_path, protected_path, output):
    with np.load(dem_path, allow_pickle=False) as data:
        elevation = data["elevation_m"]
        origin_lon = float(data["origin_lon"])
        origin_lat = float(data["origin_lat"])
        resolution = float(data["cell_degrees"])
    if (
        elevation.ndim != 2
        or min(elevation.shape) < 2
        or not np.isfinite(elevation).all()
        or not 0 < resolution <= 1
    ):
        raise ValueError(
            "Geography requires finite terrain and a valid two-dimensional grid"
        )
    transform = from_origin(
        origin_lon - resolution / 2,
        origin_lat + (elevation.shape[0] - 0.5) * resolution,
        resolution,
        resolution,
    )
    layers = {}
    sources = {"elevation": str(Path(dem_path).resolve())}
    for name, path in (
        ("water", water_path),
        ("buildings", buildings_path),
        ("protected", protected_path),
    ):
        document = json.loads(Path(path).read_text())
        if document.get("type") != "FeatureCollection":
            raise ValueError(
                "Geography masks must be GeoJSON FeatureCollections in WGS84"
            )
        if document.get("crs"):
            raise ValueError(
                "Reproject geography to WGS84 and remove the legacy CRS member"
            )
        features = [shape(feature["geometry"]) for feature in document["features"]]
        if any(
            item.geom_type not in {"Polygon", "MultiPolygon"} or not item.is_valid
            for item in features
        ):
            raise ValueError("Geography masks require valid polygons")
        geometries = [
            item.buffer(
                resolution * (1e-7 if name == "water" else 0.001), join_style="mitre"
            )
            for item in features
            if not item.is_empty
        ]
        layers[name] = (
            rasterize(
                geometries,
                out_shape=elevation.shape,
                transform=transform,
                all_touched=name != "water",
                fill=0,
                default_value=1,
                dtype="uint8",
                skip_invalid=False,
            )[::-1].astype(bool)
            if geometries
            else np.zeros(elevation.shape, dtype=bool)
        )
        sources[name] = str(Path(path).resolve())
    surface = RasterGeography(
        origin_lon,
        origin_lat,
        resolution,
        elevation,
        layers["buildings"] | layers["protected"],
        layers["water"],
        sources,
    )
    payload = {
        key: value.tolist() if isinstance(value, np.ndarray) else value
        for key, value in vars(surface).items()
    }
    Path(output).write_text(json.dumps(payload))


def main():
    parser = argparse.ArgumentParser(
        description="Prepare sourced WGS84 corridor raster. DEM NPZ keys: elevation_m, origin_lon, origin_lat, cell_degrees. Masks: GeoJSON polygon FeatureCollections; empty means explicitly verified absent within DEM coverage."
    )
    for name in ("dem", "water", "buildings", "protected", "output"):
        parser.add_argument(f"--{name}", required=True)
    args = parser.parse_args()
    prepare(args.dem, args.water, args.buildings, args.protected, args.output)


if __name__ == "__main__":
    main()
