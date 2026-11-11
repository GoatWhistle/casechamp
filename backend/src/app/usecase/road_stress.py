from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Protocol

from app.usecase.road_consequences import RegionalConsequences
from app.usecase.road_geometry import RoadGeometry


@dataclass(frozen=True)
class StressPoint:
    id: str
    name: str
    region: str
    population: int
    node: int
    snap_km: float
    longitude: float
    latitude: float


@dataclass(frozen=True)
class StressMarketChange:
    market: str
    before_hours: float
    after_hours: float | None


@dataclass(frozen=True)
class StressImpact:
    point: StressPoint
    lost_markets: int
    external_isolation: bool
    delay_minutes: float
    worst_market: str
    markets: list[StressMarketChange] = field(default_factory=list)


@dataclass(frozen=True)
class StressRegion:
    name: str
    settlements: int
    population: int
    isolated_population: int


@dataclass(frozen=True)
class StressJob:
    id: str
    version: str
    way_ids: list[int]
    parent_id: str | None = None
    status: str = "queued"
    stage: str = "preparing"
    completed: int = 0
    total: int = 180
    points: int = 0
    unbound_points: int = 0
    regions: list[StressRegion] = field(default_factory=list)
    error: str | None = None
    preexisting_isolated_points: int = 0
    newly_isolated_points: int = 0


@dataclass(frozen=True)
class StressTotals:
    affected_points: int
    exposed_population: int
    isolated_points: int
    isolated_population: int
    max_delay_minutes: float
    affected_regions: int


@dataclass(frozen=True)
class StressSummary:
    id: str
    version: str
    status: str
    stage: str
    way_count: int
    parent_id: str | None
    region: str
    totals: StressTotals | None
    snapshot_points: int
    unbound_points: int
    preexisting_isolated_points: int
    completed: int
    total: int
    consequences: RegionalConsequences | None = None


@dataclass(frozen=True)
class StressRoute:
    status: str
    hours: float | None
    km: float | None
    coordinates: list[list[float]]


@dataclass(frozen=True)
class StressRouteComparison:
    origin: StressPoint
    destination: StressPoint
    before: StressRoute
    after: StressRoute


class StressStore(Protocol):
    def consequences(self, job_id: str, region: str) -> RegionalConsequences: ...
    def totals(self, job_id: str, region: str = "") -> StressTotals: ...
    def baseline(self, version: str) -> Iterator[tuple[int, list[float]]]: ...
    def save_baseline(self, version: str, market: int, times: list[float]) -> None: ...
    def points(self) -> list[StressPoint]: ...
    def save(self, job: StressJob) -> None: ...
    def load(self) -> list[StressJob]: ...
    def save_impacts(self, job_id: str, impacts: list[StressImpact]) -> None: ...
    def impacts(self, job_id: str, region: str = "", offset: int = 0, limit: int = 200,
                bounds: tuple[float, float, float, float] | None = None) -> list[StressImpact]: ...


class StressPort(Protocol):
    def summary(self, job_id: str, region: str = "") -> StressSummary: ...
    def geometry(self, job_id: str) -> RoadGeometry: ...
    def submit(self, way_ids: list[int], parent_id: str | None = None) -> StressJob: ...
    def get(self, job_id: str) -> StressJob: ...
    def recent(self) -> list[StressJob]: ...
    def cancel(self, job_id: str) -> StressJob: ...
    def impacts(self, job_id: str, region: str, offset: int, limit: int,
                bounds: tuple[float, float, float, float] | None = None) -> list[StressImpact]: ...
    def route(self, job_id: str, origin: str, destination: str) -> StressRouteComparison: ...
