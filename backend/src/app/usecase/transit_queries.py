from collections.abc import Callable
from dataclasses import dataclass, replace
from typing import Protocol

from app.domain.errors import InvalidQuery
from app.usecase.transit_access import TransitAccess, TransitAccessResult
from app.usecase.transit_catalog import TransitCatalog, TransitStop
from app.usecase.transit_walking import TransitWalkingPort, WalkingPoint


@dataclass(frozen=True)
class TransitPlace:
    id: str
    name: str
    latitude: float | None
    longitude: float | None
    coordinate_status: str


class TransitLocations(Protocol):
    def origin(self, region: str, identifier: str, revision: str) -> TransitPlace: ...
    def facility(self, region: str, identifier: str) -> TransitPlace: ...


@dataclass(frozen=True)
class TransitCoverage:
    snapshot_id: str
    source_date: str
    source_url: str
    clock_basis: str
    stops: list[TransitStop]
    located_stops: int
    within_region_connections: int
    coverage_complete: bool = False
    operating_service_verified: bool = False


@dataclass(frozen=True)
class TransitPlan:
    coverage: TransitCoverage
    origin: TransitPlace
    destination: TransitPlace
    result: TransitAccessResult
    clock_scope: str = 'within_region_source_clocks'


class TransitQueries:
    def __init__(self, catalog: TransitCatalog, locations: TransitLocations,
                 walking: Callable[[str], TransitWalkingPort]) -> None:
        self.catalog = catalog
        self.locations = locations
        self.walking = walking

    def coverage(self, region: str) -> TransitCoverage:
        snapshot = self.catalog.latest()
        stops = [stop for stop in snapshot.stops if stop.region_id == region]
        identifiers = {stop.id for stop in stops}
        count = sum(row.source in identifiers and row.target in identifiers for row in snapshot.connections)
        return TransitCoverage(snapshot.id, snapshot.source_date, snapshot.source_url, snapshot.clock_basis,
                               stops, sum(stop.latitude is not None and stop.longitude is not None for stop in stops), count)

    def plan(self, region: str, origin_id: str, facility_id: str, departure_seconds: int,
             horizon_seconds: int = 86400, maximum_walk_metres: float = 3000.,
             transfer_seconds: int = 300) -> TransitPlan:
        if not 0 <= departure_seconds < 86400 or not 1 <= horizon_seconds <= 172800:
            raise InvalidQuery('Use a source-clock departure within one day and a horizon up to two days')
        if not 0 <= transfer_seconds <= 3600 or not 0 < maximum_walk_metres <= 10000:
            raise InvalidQuery('Walking and transfer limits are outside the supported range')
        snapshot = self.catalog.latest()
        coverage = self.coverage(region)
        if snapshot.id != coverage.snapshot_id:
            raise InvalidQuery('Transit snapshot changed; retry with the current snapshot')
        walking = self.walking(region)
        origin = self.locations.origin(region, origin_id, walking.revision)
        destination = self.locations.facility(region, facility_id)
        identifiers = {stop.id for stop in coverage.stops}
        selected = [row for row in snapshot.connections if row.source in identifiers and row.target in identifiers]
        horizon = departure_seconds + horizon_seconds
        connections = [replace(row, trip_id=f'{row.trip_id}:day-{day}', departure=row.departure + day * 86400,
                               arrival=row.arrival + day * 86400)
                       for day in range(horizon // 86400 + 1) for row in selected]
        result = TransitAccess(walking).run(
            WalkingPoint(origin.id, origin.latitude, origin.longitude, 150.),
            WalkingPoint(destination.id, destination.latitude, destination.longitude, 250.),
            [WalkingPoint(stop.id, stop.latitude, stop.longitude, 250.) for stop in coverage.stops],
            connections, departure_seconds, horizon, maximum_walk_metres, transfer_seconds,
        )
        return TransitPlan(coverage, origin, destination, result)
