from dataclasses import dataclass, replace
from math import isfinite
from typing import Literal

from app.domain.errors import InvalidQuery
from app.domain.transit_journey import (
    JourneyLeg,
    TransitConnection,
    TransitJourney,
    earliest_journey,
)
from app.usecase.transit_walking import TransitWalkingPort, WalkingLink, WalkingPoint


@dataclass(frozen=True)
class TransitAccessResult:
    status: Literal['available', 'no_journey_in_covered_data']
    journey: TransitJourney | None
    walking_revision: str
    walking_links: list[WalkingLink]
    stops_with_coordinates: int
    stops_without_coordinates: int
    timetable_stop_count: int
    timetable_stops_without_coordinates: int
    departure: int
    horizon: int
    maximum_walk_metres: float
    walking_speed_metres_per_second: float
    transfer_seconds: int
    coverage_complete: bool = False


class TransitAccess:
    def __init__(self, walking: TransitWalkingPort) -> None:
        self.walking = walking

    def run(self, origin: WalkingPoint, destination: WalkingPoint, stops: list[WalkingPoint],
            connections: list[TransitConnection], departure: int, horizon: int,
            maximum_walk_metres: float = 3000., transfer_seconds: int = 300) -> TransitAccessResult:
        points = [origin, destination, *stops]
        if len({point.id for point in points}) != len(points):
            raise InvalidQuery('Origin, destination and stop identifiers must be distinct')
        pairs = [(origin.id, destination.id)]
        pairs += [(origin.id, stop.id) for stop in stops]
        pairs += [(stop.id, destination.id) for stop in stops]
        pairs += [(left.id, right.id) for left in stops for right in stops if left.id != right.id]
        measured = self.walking.measure(points, pairs, maximum_walk_metres)
        seconds = {(link.source, link.target): link.seconds for link in measured if link.seconds is not None}
        access, egress, transfers = {}, {}, {}
        for stop in stops:
            if (origin.id, stop.id) in seconds:
                access[stop.id] = seconds[origin.id, stop.id]
            if (stop.id, destination.id) in seconds:
                egress[stop.id] = seconds[stop.id, destination.id]
            transfers[stop.id] = {target.id: seconds[stop.id, target.id] for target in stops
                                  if (stop.id, target.id) in seconds}
        result = earliest_journey(connections, access, egress, departure, horizon, transfer_seconds, transfers)
        direct = seconds.get((origin.id, destination.id))
        if direct is not None and departure + direct <= horizon and (result is None or departure + direct <= result.arrival):
            result = TransitJourney(departure, departure + direct, 0,
                                         (JourneyLeg('walk', origin.id, destination.id, departure, departure + direct),))
        if result is not None:
            result = replace(result, legs=tuple(replace(
                leg, source=origin.id if leg.source == 'origin' else leg.source,
                target=destination.id if leg.target == 'destination' else leg.target,
            ) for leg in result.legs))
        located = {stop.id for stop in stops if stop.latitude is not None and stop.longitude is not None
                   and isfinite(stop.latitude) and isfinite(stop.longitude)}
        timetable_stops = {stop for row in connections for stop in (row.source, row.target)}
        return TransitAccessResult('available' if result else 'no_journey_in_covered_data', result,
                                   self.walking.revision, measured, len(located), len(stops) - len(located),
                                   len(timetable_stops), len(timetable_stops - located), departure, horizon,
                                   maximum_walk_metres, self.walking.speed, transfer_seconds)
