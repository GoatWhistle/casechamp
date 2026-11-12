import math
import time

import numpy as np
from rasterio.features import rasterize
from rasterio.transform import from_origin
from shapely.geometry import LineString
from synthetic_traffic.geography import polyline_km


class AlignmentRejected(ValueError):
    def __init__(self, stage, failure):
        self.stage = stage
        self.reason = failure.get("reason", "unsupported_alignment")
        self.cells = sorted(
            {tuple(cell) for cell in failure.get("cells", []) if cell is not None}
        )
        super().__init__(f"Alignment rejected at {stage}: {self.reason}")


def mark_rejection(failure, reason, cells):
    if failure is not None:
        failure.update(
            reason=reason, cells=[cell for cell in cells if cell is not None]
        )


def checkpoint(deadline=None, check=None):
    if check:
        check()
    if deadline is not None and time.monotonic() >= deadline:
        raise TimeoutError("Alignment screening reached generation deadline")


def structure_cells(surface, route):
    return {
        surface.cell(*item["coordinate"]): item["kind"]
        for item in route.get("structures", [])
        if item.get("coordinate") and item.get("kind") in {"bridge", "tunnel"}
    }


def segment_details(surface, a, b, structures=None, failure=None):
    resolution = surface.cell_degrees
    points = np.asarray([a, b], dtype=float)
    x = (points[:, 0] - surface.origin_lon) / resolution
    y = (points[:, 1] - surface.origin_lat) / resolution
    left, right = math.ceil(x.min() - 0.5 - 1e-8), math.floor(x.max() + 0.5 + 1e-8)
    bottom, top = math.ceil(y.min() - 0.5 - 1e-8), math.floor(y.max() + 0.5 + 1e-8)
    rows, cols = surface.blocked.shape
    if left < 0 or bottom < 0 or right >= cols or top >= rows:
        return mark_rejection(failure, "coverage", [surface.cell(*a), surface.cell(*b)])
    geometry = LineString(points).buffer(
        resolution * 0.001, cap_style="square", join_style="mitre"
    )
    mask = rasterize(
        [geometry],
        out_shape=(top - bottom + 1, right - left + 1),
        transform=from_origin(
            surface.origin_lon + (left - 0.5) * resolution,
            surface.origin_lat + (top + 0.5) * resolution,
            resolution,
            resolution,
        ),
        all_touched=True,
        dtype="uint8",
    )[::-1].astype(bool)
    rr, cc = np.nonzero(mask)
    cells = {
        (int(row + bottom), int(col + left)) for row, col in zip(rr, cc, strict=True)
    }
    structures = structures or {}
    grade = 0.0
    mode = next((structures[cell] for cell in cells if cell in structures), None)
    for row, col in cells:
        if surface.blocked[row, col] or not np.isfinite(surface.elevation_m[row, col]):
            return mark_rejection(failure, "blocked_or_missing_terrain", [(row, col)])
        if surface.water[row, col]:
            if structures.get((row, col)) != "bridge":
                return mark_rejection(failure, "unmarked_water", [(row, col)])
            mode = "bridge"
    count = max(1, math.ceil(max(abs(x[1] - x[0]), abs(y[1] - y[0])) * 4))
    sampled = np.linspace(points[0], points[1], count + 1)
    elevations = []
    for point in sampled:
        gx, gy = (
            (point[0] - surface.origin_lon) / resolution,
            (point[1] - surface.origin_lat) / resolution,
        )
        col, row = math.floor(gx), math.floor(gy)
        dx, dy = gx - col, gy - row
        value = 0.0
        for dr, dc, weight in (
            (0, 0, (1 - dx) * (1 - dy)),
            (0, 1, dx * (1 - dy)),
            (1, 0, (1 - dx) * dy),
            (1, 1, dx * dy),
        ):
            if weight < 1e-10:
                continue
            if not 0 <= row + dr < rows or not 0 <= col + dc < cols:
                return mark_rejection(
                    failure, "terrain_coverage", [surface.cell(*point)]
                )
            value += float(surface.elevation_m[row + dr, col + dc]) * weight
        elevations.append(value)
    for index in range(count):
        distance = (
            polyline_km([sampled[index].tolist(), sampled[index + 1].tolist()]) * 1000
        )
        slope = (
            abs(elevations[index + 1] - elevations[index]) / distance
            if distance
            else 0.0
        )
        grade = max(grade, slope)
        if slope > surface.max_grade:
            touched = [surface.cell(*sampled[index]), surface.cell(*sampled[index + 1])]
            if not any(
                structures.get(cell) in {"tunnel", "bridge"} for cell in touched
            ):
                return mark_rejection(failure, "terrain_grade", touched)
            mode = mode or "tunnel"
    return {
        "maximum_terrain_grade": grade,
        "structure": mode,
        "checked_cells": len(cells),
    }


def record_alignment_attempt(result, rejected, used):
    result["alignment_rejections"] = result.get("alignment_rejections", 0) + len(
        rejected
    )
    result["alignment_retry_attempts"] = result.get(
        "alignment_retry_attempts", 0
    ) + max(0, used - 1)
    locations = result.setdefault("alignment_failure_locations", [])
    locations.extend(rejected[: max(0, 32 - len(locations))])
