from dataclasses import dataclass, field
from math import isfinite
from typing import Protocol

from app.domain.errors import DataUnavailable, InvalidQuery, RegionNotFound
from app.domain.road_economics import MoneyAssumptions, MoneyEffect
from app.usecase.interface import AtlasRepository
from app.usecase.transport_links import LinkChange, PlaceName, TransportLink, validate_links


@dataclass(frozen=True)
class RoadSegment:
    way_id: int
    name: str
    highway: str
    speed_kmh: float
    coordinates: list[list[float]]
    source_node: int | None = None
    target_node: int | None = None


@dataclass(frozen=True)
class GraphLocation:
    point_id: str
    name: str
    region: str
    node: int | None
    longitude: float
    latitude: float
    snap_km: float


@dataclass(frozen=True)
class RoadView:
    segments: list[RoadSegment]
    matched: int
    truncated: bool
    version: str
    detail: str = "all"


@dataclass(frozen=True)
class RoadChange:
    way_id: int
    speed_factor: float


@dataclass(frozen=True)
class RoadAddition:
    source_node: int
    target_node: int
    travel_hours: float
    coordinates: list[list[float]] | None = None


@dataclass(frozen=True)
class SettlementEffect:
    point_id: str
    before: float
    after: float
    delta: float


@dataclass(frozen=True)
class RoadResult:
    before: float
    after: float
    delta: float
    relative_percent: float | None
    population: int
    settlements: int
    changed_edges: int
    normalization: float
    elapsed_seconds: float
    affected_settlements: int | None = None
    money: MoneyEffect | None = None
    routing_method: str = "full_graph"
    settlement_effects: list[SettlementEffect] = field(default_factory=list)


@dataclass(frozen=True)
class RoadJob:
    id: str
    region_id: str
    region: str
    scenario: str
    changes: list[RoadChange]
    status: str
    completed: int
    total: int
    version: str
    result: RoadResult | None = None
    error: str | None = None
    addition: RoadAddition | None = None
    money_assumptions: MoneyAssumptions | None = None
    links: list[LinkChange] = field(default_factory=list)


class RoadGraphPort(Protocol):
    def locations(self, query: str, region_id: str | None) -> list[GraphLocation]: ...
    def view(self, bounds: tuple[float, float, float, float], zoom: float) -> RoadView: ...
    def submit(
        self,
        region_id: str,
        region: str,
        scenario: str,
        changes: list[RoadChange],
        links: list[LinkChange] | None = None,
        *,
        queue: bool = False,
    ) -> RoadJob: ...
    def transport_links(
        self, network: str, scenario: str, place: str, mode: str | None
    ) -> list[TransportLink]: ...
    def place_names(self, ids: list[str]) -> list[PlaceName]: ...
    def submit_addition(
        self, region_id: str, region: str, addition: RoadAddition, money: MoneyAssumptions | None
    ) -> RoadJob: ...
    def recent(self) -> list[RoadJob]: ...
    def job(self, job_id: str) -> RoadJob: ...
    def cancel(self, job_id: str) -> RoadJob: ...


class RoadViewSource(Protocol):
    def view(self, bounds: tuple[float, float, float, float], zoom: float) -> RoadView: ...


class RoadGraph:
    def __init__(
        self,
        engine: RoadGraphPort | None,
        atlas: AtlasRepository,
        view_source: RoadViewSource | None = None,
    ) -> None:
        self._engine = engine
        self.atlas = atlas
        self.view_source = view_source

    @property
    def engine(self) -> RoadGraphPort:
        if self._engine is None:
            raise DataUnavailable("GRAPH_DIR is not configured")
        return self._engine

    def locations(self, query: str, region_id: str | None = None) -> list[GraphLocation]:
        if not 2 <= len(query.strip()) <= 100:
            raise InvalidQuery("Place query must contain between 2 and 100 characters")
        return self.engine.locations(query.strip(), region_id)

    def recent(self) -> list[RoadJob]:
        return self.engine.recent()

    def view(self, west: float, south: float, east: float, north: float, zoom: float) -> RoadView:
        if not all(isfinite(v) for v in (west, south, east, north, zoom)):
            raise InvalidQuery()
        if not (-180 <= west < east <= 180 and -85 <= south < north <= 85 and 0 <= zoom <= 22):
            raise InvalidQuery()
        source = self.view_source if self.view_source is not None else self.engine
        return source.view((west, south, east, north), zoom)

    def transport_links(
        self, network: str, scenario: str, place: str, mode: str | None = None
    ) -> list[TransportLink]:
        if network not in {"intercity", "local"} or scenario not in {"road", "summer", "winter"}:
            raise InvalidQuery("Сеть: intercity или local; сценарий: road, summer или winter")
        if not 2 <= len(place.strip()) <= 100:
            raise InvalidQuery("Укажите город, населённый пункт или регион")
        return self.engine.transport_links(network, scenario, place.strip(), mode)

    def place_names(self, ids: list[str]) -> list[PlaceName]:
        if not 1 <= len(ids) <= 60:
            raise InvalidQuery("Укажите от 1 до 60 ID населённых пунктов")
        return self.engine.place_names(sorted(set(ids)))

    def submit(
        self,
        region_id: str,
        scenario: str,
        changes: list[RoadChange],
        links: list[LinkChange] | None = None,
        *,
        queue: bool = False,
    ) -> RoadJob:
        links = links or []
        if scenario not in {"road", "summer", "winter"} or len(changes) > 50 or len(links) > 30:
            raise InvalidQuery()
        if not changes and not links:
            raise InvalidQuery("Укажите изменения дорог или связей")
        validate_links(links)
        if len({c.way_id for c in changes}) != len(changes):
            raise InvalidQuery("Duplicate road identifiers")
        if any(
            c.way_id < 0 or not isfinite(c.speed_factor) or not 0 <= c.speed_factor <= 3
            for c in changes
        ):
            raise InvalidQuery("Speed factor must be between 0 (closure) and 3")
        region = next((r for r in self.atlas.regions() if r.id == region_id), None)
        if region is None:
            raise RegionNotFound()
        return self.engine.submit(region_id, region.name, scenario, changes, links, queue=queue)

    def add_connection(
        self, region_id: str, addition: RoadAddition, money: MoneyAssumptions | None = None
    ) -> RoadJob:
        if (
            addition.source_node < 0
            or addition.target_node < 0
            or addition.source_node == addition.target_node
            or not isfinite(addition.travel_hours)
            or not 0 < addition.travel_hours <= 72
        ):
            raise InvalidQuery("Specify two distinct graph nodes and a travel time in (0,72] hours")
        if money and any(
            not isfinite(v) or v < 0
            for v in (
                money.trips_per_year,
                money.rub_per_hour,
                money.capital_cost_rub,
                money.annual_operating_cost_rub,
            )
        ):
            raise InvalidQuery("Economic assumptions must be finite and nonnegative")
        region = next((r for r in self.atlas.regions() if r.id == region_id), None)
        if region is None:
            raise RegionNotFound()
        return self.engine.submit_addition(region_id, region.name, addition, money)

    def job(self, job_id: str) -> RoadJob:
        return self.engine.job(job_id)

    def cancel(self, job_id: str) -> RoadJob:
        return self.engine.cancel(job_id)
