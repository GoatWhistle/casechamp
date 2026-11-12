import json
from math import ceil, floor, isfinite
from pathlib import Path

from shapely import affinity, make_valid
from shapely.geometry import Polygon, box
from synthetic_traffic.geography_queue_store import (
    connect,
    exclusive,
    metadata,
    now,
    state,
    status,
)


def _unwrap(ring):
    result = []
    for coordinate in ring:
        if len(coordinate) != 2:
            raise ValueError("Boundary coordinates must contain longitude and latitude")
        lon, lat = map(float, coordinate)
        if not isfinite(lon) or not isfinite(lat) or not -90 <= lat <= 90:
            raise ValueError("Invalid boundary coordinate")
        lon = (lon + 180) % 360 - 180
        if result:
            lon += 360 * round((result[-1][0] - lon) / 360)
        result.append((lon, lat))
    if len(result) < 4 or result[0] != result[-1]:
        raise ValueError(
            "Boundary rings must be closed and contain at least four coordinates"
        )
    return result


def tiles_for(boundary):
    result = set()
    for rings in boundary["polygons"]:
        if not rings:
            raise ValueError("Boundary polygon has no shell")
        shell = _unwrap(rings[0])
        center = sum(point[0] for point in shell) / len(shell)
        holes = []
        for ring in rings[1:]:
            hole = _unwrap(ring)
            shift = 360 * round((center - sum(p[0] for p in hole) / len(hole)) / 360)
            holes.append([(lon + shift, lat) for lon, lat in hole])
        polygon = make_valid(Polygon(shell, holes))
        for shift in (-360, 0, 360):
            clipped = affinity.translate(polygon, xoff=shift).intersection(
                box(-180, -90, 180, 90)
            )
            if clipped.is_empty or clipped.area <= 0:
                continue
            west, south, east, north = clipped.bounds
            for x in range(
                max(0, floor((west + 180) * 2)), min(720, ceil((east + 180) * 2))
            ):
                for y in range(
                    max(0, floor((south + 90) * 2)), min(360, ceil((north + 90) * 2))
                ):
                    tile = box(x / 2 - 180, y / 2 - 90, x / 2 - 179.5, y / 2 - 89.5)
                    if clipped.intersects(tile) and clipped.intersection(tile).area > 0:
                        result.add((x, y))
    if not result:
        raise ValueError(f"Boundary has no positive-area tiles: {boundary['id']}")
    return result


def plan(boundaries, output, priority_bbox=None):
    focus = None
    if priority_bbox is not None:
        if len(priority_bbox) != 4 or not all(
            isfinite(float(value)) for value in priority_bbox
        ):
            raise ValueError("Priority bounds require four finite coordinates")
        west, south, east, north = map(float, priority_bbox)
        if not (-180 <= west < east <= 180 and -90 <= south < north <= 90):
            raise ValueError("Priority bounds must be an ordered geographic rectangle")
        priority_bbox = [west, south, east, north]
        focus = box(*priority_bbox)
    if isinstance(boundaries, (str, Path)):
        boundaries = json.loads(Path(boundaries).read_text())
    if isinstance(boundaries, dict):
        boundaries = boundaries.get("regions")
    if not isinstance(boundaries, list) or not boundaries:
        raise ValueError("Planning requires a nonempty atlas boundary list")
    ids = [str(boundary["id"]) for boundary in boundaries]
    if len(set(ids)) != len(ids):
        raise ValueError("Atlas boundary identifiers must be unique")
    ordered = sorted(
        boundaries, key=lambda row: (str(row["id"]) != "07000000", str(row["id"]))
    )
    tiles = {}
    for index, boundary in enumerate(ordered):
        for coordinate in tiles_for(boundary):
            entry = tiles.setdefault(coordinate, {"priority": index, "regions": []})
            entry["regions"].append(str(boundary["id"]))
    with exclusive(output) as root, connect(root) as db:
        db.execute("UPDATE tiles SET active=0")
        db.execute("DELETE FROM regions")
        for boundary in ordered:
            db.execute(
                "INSERT INTO regions VALUES(?,?,?)",
                (
                    str(boundary["id"]),
                    str(boundary["name"]),
                    json.dumps(boundary["bounds"]),
                ),
            )
        for (x, y), entry in sorted(tiles.items()):
            identifier = f"x{x:04d}-y{y:03d}"
            bounds = [x / 2 - 180, y / 2 - 90, x / 2 - 179.5, y / 2 - 89.5]
            priority = entry["priority"]
            if focus is not None:
                priority += 1
                if "07000000" in entry["regions"]:
                    priority = 0 if box(*bounds).intersection(focus).area > 0 else 1
            db.execute(
                """INSERT INTO tiles(id,bbox,region_ids,priority,updated_at) VALUES(?,?,?,?,?)
                ON CONFLICT(id) DO UPDATE SET bbox=excluded.bbox,region_ids=excluded.region_ids,
                priority=excluded.priority,active=1""",
                (
                    identifier,
                    json.dumps(bounds),
                    json.dumps(entry["regions"]),
                    priority,
                    now(),
                ),
            )
        metadata(
            db,
            "coverage",
            {
                "source": "provided_atlas_boundaries",
                "region_count": len(ids),
                "region_ids": [str(row["id"]) for row in ordered],
                "tile_degrees": 0.5,
                "resolution_degrees": 0.001,
                "coverage_claim": "provided_atlas_regions_only",
                "priority_bbox": priority_bbox,
            },
        )
        state(db, "planned")
    return status(output)
