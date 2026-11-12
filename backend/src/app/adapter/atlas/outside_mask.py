import json
from functools import lru_cache

from shapely import make_valid
from shapely.affinity import translate
from shapely.geometry import MultiPolygon, Polygon, box
from shapely.geometry.base import BaseGeometry
from shapely.ops import unary_union

from app.usecase.dto import BoundaryShape
from app.usecase.municipalities import MunicipalCoordinates


def _ring(points: list[list[float]], center: float | None = None) -> list[tuple[float, float]]:
    result: list[tuple[float, float]] = []
    for lon, lat in points:
        anchor = result[-1][0] if result else center
        if anchor is not None:
            lon += 360 * round((anchor - lon) / 360)
        result.append((lon, lat))
    return result


def _polygons(shape: BaseGeometry) -> list[Polygon]:
    if isinstance(shape, Polygon):
        return [shape]
    if hasattr(shape, "geoms"):
        return [polygon for part in shape.geoms for polygon in _polygons(part)]
    return []


@lru_cache(maxsize=2)
def _mask(payload: str) -> MunicipalCoordinates:
    world = box(-180, -90, 180, 90)
    pieces = []
    for coordinates in json.loads(payload):
        for rings in coordinates:
            exterior = _ring(rings[0])
            center = sum(point[0] for point in exterior) / len(exterior)
            polygon = make_valid(Polygon(exterior, [_ring(ring, center) for ring in rings[1:]]))
            for offset in (-720, -360, 0, 360, 720):
                shifted = translate(polygon, xoff=offset)
                if shifted.intersects(world):
                    pieces.append(shifted.intersection(world))
    land = unary_union(pieces)
    outside = MultiPolygon(_polygons(world.difference(land)))
    return [
        [
            [(point[0], point[1]) for point in polygon.exterior.coords],
            *[[(point[0], point[1]) for point in ring.coords] for ring in polygon.interiors],
        ]
        for polygon in outside.geoms
    ]


class AtlasOutsideMask:
    def __call__(self, boundaries: list[BoundaryShape]) -> MunicipalCoordinates:
        return _mask(json.dumps([item.polygons for item in boundaries], separators=(",", ":")))
