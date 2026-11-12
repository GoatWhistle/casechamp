import json
import math
from pathlib import Path

import numpy as np


def read_tile(path):
    path = Path(path)
    if path.suffix != ".npz":
        return json.loads(path.read_text())
    with np.load(path, allow_pickle=False) as data:
        metadata = json.loads(str(data["metadata"].item()))
        return {
            **metadata,
            **{key: data[key].copy() for key in ("elevation_m", "blocked", "water")},
        }


def _entries(directory):
    catalog = directory / "catalog.json"
    if catalog.is_file():
        document = json.loads(catalog.read_text())
        return document.get("tiles", [])
    entries = []
    for path in directory.rglob("manifest.json"):
        manifest = json.loads(path.read_text())
        if manifest.get("status") == "complete" and manifest.get("bbox"):
            tile = path.parent / manifest.get("geography_file", "geography.npz")
            entries.append(
                {"path": str(tile.relative_to(directory)), "bbox": manifest["bbox"]}
            )
    return entries


def mosaic_payload(directory, bounds):
    directory = Path(directory)
    if bounds is None:
        raise ValueError(
            "A tile catalog requires selected bounds; loading all tiles is disabled"
        )
    bounds = np.asarray(bounds, dtype=float)
    if bounds.shape != (4,) or not np.isfinite(bounds).all():
        raise ValueError("Selected bounds require four finite geographic coordinates")
    west, south, east, north = map(float, bounds)
    if not -180 <= west < east <= 180 or not -90 <= south < north <= 90:
        raise ValueError("Selected bounds must be an ordered WGS84 rectangle")
    selected = []
    for entry in _entries(directory):
        left, bottom, right, top = entry["bbox"]
        if right < west or left > east or top < south or bottom > north:
            continue
        path = (directory / entry["path"]).resolve()
        if not path.is_relative_to(directory.resolve()) or not path.is_file():
            raise ValueError("Geography catalog references a missing or external tile")
        selected.append(path)
    if not selected:
        raise ValueError("No completed geographic tiles cover the selected bounds")
    first = read_tile(selected[0])
    resolution = float(first["cell_degrees"])
    origin_lon = math.floor(west / resolution + 1e-8) * resolution
    origin_lat = math.floor(south / resolution + 1e-8) * resolution
    cols = math.ceil((east - origin_lon) / resolution - 1e-8) + 1
    rows = math.ceil((north - origin_lat) / resolution - 1e-8) + 1
    if rows * cols > 25_000_000:
        raise ValueError(
            "Selected geography exceeds 25 million cells; narrow the network scope"
        )
    constraints = {"max_grade": 0.08, "max_bridge_km": 5.0, "max_tunnel_km": 20.0}
    elevation = np.zeros((rows, cols), dtype=np.float32)
    blocked = np.ones((rows, cols), dtype=bool)
    water = np.zeros((rows, cols), dtype=bool)
    covered = np.zeros((rows, cols), dtype=bool)
    sources = {key: [] for key in ("elevation", "water", "buildings", "protected")}
    openings = []
    for index, path in enumerate(selected):
        tile = first if index == 0 else read_tile(path)
        if not np.isclose(tile["cell_degrees"], resolution, rtol=0, atol=1e-12):
            raise ValueError("Geography tiles must share a grid resolution")
        offset = np.array(
            [
                (tile["origin_lat"] - origin_lat) / resolution,
                (tile["origin_lon"] - origin_lon) / resolution,
            ]
        )
        if not np.allclose(offset, np.round(offset), rtol=0, atol=1e-5):
            raise ValueError("Geography tiles must have globally aligned grid origins")
        row, col = map(int, np.round(offset))
        values = np.asarray(tile["elevation_m"], dtype=np.float32)
        if values.ndim != 2 or not np.isfinite(values).all():
            raise ValueError("A completed tile has invalid terrain coverage")
        height, width = values.shape
        dr = slice(max(0, row), min(rows, row + height))
        dc = slice(max(0, col), min(cols, col + width))
        if dr.start >= dr.stop or dc.start >= dc.stop:
            continue
        sr = slice(dr.start - row, dr.stop - row)
        sc = slice(dc.start - col, dc.stop - col)
        present = covered[dr, dc]
        elevation[dr, dc] = np.where(present, elevation[dr, dc], values[sr, sc])
        tile_blocked = np.asarray(tile["blocked"], dtype=bool)[sr, sc]
        blocked[dr, dc] = np.where(
            present, blocked[dr, dc] | tile_blocked, tile_blocked
        )
        water[dr, dc] |= np.asarray(tile["water"], dtype=bool)[sr, sc]
        covered[dr, dc] = True
        for key, records in sources.items():
            if not tile["sources"].get(key):
                raise ValueError("A tile lacks required geographic provenance")
            records.append(
                {
                    "tile": str(path.relative_to(directory.resolve())),
                    "source": tile["sources"][key],
                }
            )
        openings.extend(tile.get("openings", []))
        for key, value in constraints.items():
            constraints[key] = min(value, float(tile.get(key, value)))
    sources["coverage"] = {
        "selected_bounds": list(bounds),
        "covered_cells": int(covered.sum()),
        "uncovered_blocked_cells": int((~covered).sum()),
        "loaded_tiles": len(selected),
    }
    return {
        "origin_lon": origin_lon,
        "origin_lat": origin_lat,
        "cell_degrees": resolution,
        "elevation_m": elevation,
        "blocked": blocked,
        "water": water,
        "sources": sources,
        "openings": openings,
        **constraints,
    }
