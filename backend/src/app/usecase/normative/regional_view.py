from dataclasses import dataclass
from math import isfinite
from typing import Literal, Protocol

from app.domain.errors import InvalidQuery
from app.domain.normative.comparison import RouteComparison
from app.domain.normative.fire import FireProfile
from app.domain.normative.measurement_definition import MeasurementDefinition
from app.domain.normative.model import AccessRow, Facility
from app.usecase.normative.regional_catalog import RegionalCatalogQueries
from app.usecase.normative.route import RouteStage

RowSort = Literal["position", "name", "cost"]


@dataclass(frozen=True, slots=True)
class RegionalRunView:
    run_id: str
    region_id: str
    region_name: str
    criterion_id: str
    category: str
    graph_revision: str
    saved_at: str
    closed_way_ids: list[int]
    comparison: RouteComparison
    model_revision: str
    mode: str
    unit: str
    qualification: str
    fire_profile: FireProfile | None
    origins: int
    baseline_measured_paths: int
    scenario_measured_paths: int
    facility_count: int
    measurement_definition: MeasurementDefinition = MeasurementDefinition.SINGLE_REFERENCE_POINT


@dataclass(frozen=True, slots=True)
class RegionalRowPage:
    run_id: str
    stage: RouteStage
    rows: list[AccessRow]
    total: int
    page: int
    page_size: int


@dataclass(frozen=True, slots=True)
class RegionalFacilityPage:
    run_id: str
    facilities: list[Facility]
    total: int
    page: int
    page_size: int


@dataclass(frozen=True, slots=True)
class RegionalPointDetail:
    row: AccessRow
    facility: Facility | None


@dataclass(frozen=True, slots=True)
class RegionalMapBounds:
    west: float
    south: float
    east: float
    north: float

    def validate(self) -> None:
        if (
            not all(isfinite(v) for v in (self.west, self.south, self.east, self.north))
            or not -180 <= self.west <= 180
            or not -180 <= self.east <= 180
            or not -90 <= self.south < self.north <= 90
        ):
            raise InvalidQuery("Map bounds require finite longitudes and ordered latitudes")


@dataclass(frozen=True, slots=True)
class RegionalMapCell:
    id: str
    latitude: float
    longitude: float
    references: int
    measured: int
    minimum: float | None
    maximum: float | None
    origin_id: str | None
    bounds: tuple[float, float, float, float]


@dataclass(frozen=True, slots=True)
class RegionalFacilityCell:
    id: str
    latitude: float
    longitude: float
    facilities: int
    facility_id: str | None
    bounds: tuple[float, float, float, float]


@dataclass(frozen=True, slots=True)
class RegionalMapView:
    run_id: str
    stage: RouteStage
    unit: str
    cells: list[RegionalMapCell]
    viewport_references: int
    facilities: list[RegionalFacilityCell]
    viewport_facilities: int


class RegionalViewRepository(Protocol):
    def latest_view(self, region_id: str, criterion_id: str) -> RegionalRunView | None: ...
    def view(self, run_id: str) -> RegionalRunView | None: ...
    def rows(
        self,
        view: RegionalRunView,
        stage: RouteStage,
        page: int,
        page_size: int,
        sort: RowSort,
        descending: bool,
        search: str,
    ) -> RegionalRowPage: ...
    def facilities(
        self, view: RegionalRunView, page: int, page_size: int, search: str
    ) -> RegionalFacilityPage: ...
    def point(
        self, view: RegionalRunView, stage: RouteStage, origin_id: str
    ) -> RegionalPointDetail | None: ...
    def map_view(
        self, view: RegionalRunView, stage: RouteStage, bounds: RegionalMapBounds, zoom: int
    ) -> RegionalMapView: ...


class RegionalViewQueries:
    def __init__(self, repository: RegionalViewRepository, catalog: RegionalCatalogQueries) -> None:
        self.repository = repository
        self.catalog = catalog

    def latest(self, region_id: str, criterion_id: str) -> RegionalRunView | None:
        self.catalog.scope(region_id, criterion_id)
        return self.repository.latest_view(region_id, criterion_id)

    def view(self, run_id: str) -> RegionalRunView:
        result = self.repository.view(run_id)
        if result is None:
            raise InvalidQuery("Unknown regional measurement")
        return result

    def rows(
        self,
        run_id: str,
        stage: RouteStage,
        page: int,
        page_size: int,
        sort: RowSort,
        descending: bool,
        search: str,
    ) -> RegionalRowPage:
        validate_page(page, page_size, search)
        return self.repository.rows(
            self.view(run_id), stage, page, page_size, sort, descending, search.strip()
        )

    def facilities(
        self, run_id: str, page: int, page_size: int, search: str
    ) -> RegionalFacilityPage:
        validate_page(page, page_size, search)
        return self.repository.facilities(self.view(run_id), page, page_size, search.strip())

    def point(self, run_id: str, stage: RouteStage, origin_id: str) -> RegionalPointDetail:
        result = self.repository.point(self.view(run_id), stage, origin_id)
        if result is None:
            raise InvalidQuery("Unknown regional measurement origin")
        return result

    def map_view(
        self, run_id: str, stage: RouteStage, bounds: RegionalMapBounds, zoom: int
    ) -> RegionalMapView:
        bounds.validate()
        if not 0 <= zoom <= 20:
            raise InvalidQuery("Map zoom must be between zero and twenty")
        return self.repository.map_view(self.view(run_id), stage, bounds, zoom)


def validate_page(page: int, page_size: int, search: str) -> None:
    if not 1 <= page <= 2147483647 or not 1 <= page_size <= 100 or len(search) > 200:
        raise InvalidQuery("Select a positive page, up to 100 rows and up to 200 search characters")
