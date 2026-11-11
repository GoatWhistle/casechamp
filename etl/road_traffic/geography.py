from collections import defaultdict
from math import isfinite

from pyproj import Geod
from shapely import STRtree, affinity, make_valid, prepare
from shapely.geometry import LineString, Polygon
from shapely.ops import unary_union

GEOD = Geod(ellps="WGS84")


def unwrap(coordinates: list) -> list[tuple[float, float]]:
    result = []
    for coordinate in coordinates:
        if len(coordinate) != 2:
            raise ValueError("Coordinates must contain longitude and latitude")
        lon, lat = map(float, coordinate)
        if not isfinite(lon) or not isfinite(lat) or not -90 <= lat <= 90:
            raise ValueError("Invalid geographic coordinate")
        lon = (lon + 180) % 360 - 180
        if result:
            lon += 360 * round((result[-1][0] - lon) / 360)
        result.append((lon, lat))
    return result


def line_km(geometry) -> float:
    if geometry.is_empty:
        return 0.0
    if geometry.geom_type in {"LineString", "LinearRing"}:
        lon, lat = geometry.xy
        return abs(GEOD.line_length(lon, lat)) / 1000
    if hasattr(geometry, "geoms"):
        return sum(line_km(part) for part in geometry.geoms)
    return 0.0


class RegionCoverage:
    def __init__(self, boundaries: list[dict]) -> None:
        self.repairs: list[dict] = []
        self.region_ids: list[str] = []
        geometries = []
        seen = set()
        for boundary in sorted(boundaries, key=lambda row: str(row["id"])):
            region_id = str(boundary["id"])
            if region_id in seen:
                raise ValueError(f"Duplicate region boundary: {region_id}")
            seen.add(region_id)
            polygons = []
            for index, rings in enumerate(boundary["polygons"]):
                if not rings or len(rings[0]) < 4:
                    raise ValueError(f"Incomplete boundary: {region_id}/{index}")
                shell = unwrap(rings[0])
                holes = []
                center = sum(x for x, _ in shell) / len(shell)
                for ring in rings[1:]:
                    if len(ring) < 4:
                        raise ValueError(
                            f"Incomplete boundary hole: {region_id}/{index}"
                        )
                    hole = unwrap(ring)
                    shift = 360 * round(
                        (center - sum(x for x, _ in hole) / len(hole)) / 360
                    )
                    holes.append([(x + shift, y) for x, y in hole])
                polygon = Polygon(shell, holes)
                if not polygon.is_valid:
                    polygon = make_valid(polygon)
                    self.repairs.append(
                        {
                            "region_id": region_id,
                            "polygon_index": index,
                            "operation": "make_valid",
                        }
                    )
                if polygon.is_empty or polygon.area == 0:
                    raise ValueError(f"Empty boundary: {region_id}/{index}")
                polygons.append(polygon)
            if not polygons:
                raise ValueError(f"Missing polygons: {region_id}")
            region = unary_union(polygons)
            parts = (
                list(region.geoms) if region.geom_type == "MultiPolygon" else [region]
            )
            for part in parts:
                for shift in (-360, 0, 360):
                    geometry = affinity.translate(part, xoff=shift)
                    prepare(geometry)
                    geometries.append(geometry)
                    self.region_ids.append(region_id)
        self.geometries = geometries
        self.tree = STRtree(geometries)

    def measure(self, coordinates: list[list[float]]) -> list[tuple[str, float]]:
        if len(coordinates) < 2:
            raise ValueError("Road geometry requires at least two coordinates")
        line = LineString(unwrap(coordinates))
        candidates = self.tree.query(line)
        by_region = defaultdict(list)
        for position in candidates:
            by_region[self.region_ids[position]].append(self.geometries[position])
        remaining = line
        result = []
        for region_id in sorted(by_region):
            parts = by_region[region_id]
            polygon = parts[0] if len(parts) == 1 else unary_union(parts)
            if polygon.covers(remaining):
                length = line_km(remaining)
                if length > 0:
                    result.append((region_id, length))
                break
            if not polygon.intersects(remaining):
                continue
            covered = remaining.intersection(polygon)
            length = line_km(covered)
            if length > 0:
                result.append((region_id, length))
                remaining = remaining.difference(polygon)
            if remaining.is_empty:
                break
        return result
