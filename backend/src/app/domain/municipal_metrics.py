from dataclasses import dataclass
from math import isfinite


@dataclass(frozen=True, slots=True)
class MunicipalObservation:
    point_id: str
    longitude: float
    latitude: float
    population: int | None
    values: dict[str, float | None]
    is_rural: bool
    node: int | None = None
    snap_km: float | None = None


@dataclass(frozen=True, slots=True)
class MunicipalMetric:
    key: str
    value: float | None
    status: str
    reason: str | None
    unit: str
    population: int
    measured_population: int
    settlements: int
    measured_settlements: int
    population_coverage: float | None


def _ring_contains(lon: float, lat: float, ring: list[tuple[float, float]]) -> bool:
    if not ring:
        return False
    points: list[tuple[float, float]] = []
    for x, y in ring:
        anchor = points[-1][0] if points else lon
        points.append((x + 360 * round((anchor - x) / 360), y))
    lon += 360 * round((points[0][0] - lon) / 360)
    inside = False
    previous = points[-1]
    for current in points:
        x1, y1 = previous
        x2, y2 = current
        cross = (lon - x1) * (y2 - y1) - (lat - y1) * (x2 - x1)
        if cross == 0 and min(x1, x2) <= lon <= max(x1, x2) and min(y1, y2) <= lat <= max(y1, y2):
            return True
        if (y1 > lat) != (y2 > lat) and lon < (x2 - x1) * (lat - y1) / (y2 - y1) + x1:
            inside = not inside
        previous = current
    return inside


def municipal_contains(
    longitude: float, latitude: float, polygons: list[list[list[tuple[float, float]]]]
) -> bool:
    return any(
        polygon
        and _ring_contains(longitude, latitude, polygon[0])
        and not any(_ring_contains(longitude, latitude, hole) for hole in polygon[1:])
        for polygon in polygons
    )


def aggregate_metric(
    observations: list[MunicipalObservation], key: str, unit: str
) -> MunicipalMetric:
    eligible = [row for row in observations if key != "rai_2km" or row.is_rural]
    population = sum(max(0, row.population or 0) for row in eligible)
    measured: list[tuple[MunicipalObservation, float]] = []
    for row in eligible:
        value = row.values.get(key)
        if value is not None and isfinite(value) and value >= 0:
            measured.append((row, value))
    measured_population = sum(max(0, row.population or 0) for row, _ in measured)
    value = (
        sum(value * max(0, row.population or 0) for row, value in measured) / measured_population
        if measured_population
        else None
    )
    return MunicipalMetric(
        key,
        value,
        "available" if value is not None else "unavailable",
        None if value is not None else "municipal_measured_population_missing",
        unit,
        population,
        measured_population,
        len(eligible),
        len(measured),
        measured_population / population if population else None,
    )


def municipal_points(
    points: list[MunicipalObservation], polygons: list[list[list[tuple[float, float]]]]
) -> list[MunicipalObservation]:
    vertices = [point for polygon in polygons for ring in polygon for point in ring]
    if not vertices:
        return []
    west, east = min(p[0] for p in vertices), max(p[0] for p in vertices)
    south, north = min(p[1] for p in vertices), max(p[1] for p in vertices)
    return [
        point
        for point in points
        if south <= point.latitude <= north
        and any(west <= point.longitude + shift <= east for shift in (-360, 0, 360))
        and municipal_contains(point.longitude, point.latitude, polygons)
    ]
