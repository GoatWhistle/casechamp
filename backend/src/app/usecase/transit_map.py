from dataclasses import dataclass
from math import isfinite
from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from app.usecase.transit_catalog import TransitStop
    from app.usecase.transit_queries import TransitPlace, TransitPlan


@dataclass(frozen=True)
class TransitMapPoint:
    id: str
    name: str
    role: Literal['origin', 'destination', 'stop']
    latitude: float
    longitude: float


@dataclass(frozen=True)
class TransitMapTarget:
    region_id: str
    snapshot_id: str
    points: tuple[TransitMapPoint, ...]
    geometry_status: str = 'stops_only_not_route_geometry'


def transit_map_target(region: str, plan: 'TransitPlan') -> TransitMapTarget:
    journey = plan.result.journey
    used = {key for leg in journey.legs for key in (leg.source, leg.target)} if journey else set()
    points = []
    places: list[tuple[TransitPlace | TransitStop, Literal['origin', 'destination', 'stop']]] = [
        (plan.origin, 'origin'), (plan.destination, 'destination')]
    places.extend((stop, 'stop') for stop in plan.coverage.stops if stop.id in used)
    for place, role in places:
        lat, lon = place.latitude, place.longitude
        if lat is None or lon is None or not isfinite(lat) or not isfinite(lon):
            continue
        if not -85 <= lat <= 85 or not -180 <= lon <= 180:
            continue
        points.append(TransitMapPoint(place.id, place.name or place.id, role, lat, lon))
    return TransitMapTarget(region, plan.coverage.snapshot_id, tuple(points))
