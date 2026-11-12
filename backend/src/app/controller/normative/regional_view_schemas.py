from pydantic import BaseModel

from app.controller.normative.router import (
    AccessResponse,
    ComparisonResponse,
    FacilityResponse,
    FireProfileInput,
)
from app.domain.normative.measurement_definition import MeasurementDefinition
from app.usecase.normative.route import RouteStage


class RegionalRunViewResponse(BaseModel):
    run_id: str
    region_id: str
    region_name: str
    criterion_id: str
    category: str
    graph_revision: str
    saved_at: str
    closed_way_ids: list[int]
    comparison: ComparisonResponse
    model_revision: str
    mode: str
    unit: str
    qualification: str
    fire_profile: FireProfileInput | None
    origins: int
    baseline_measured_paths: int
    scenario_measured_paths: int
    facility_count: int
    measurement_definition: MeasurementDefinition


class RegionalRowPageResponse(BaseModel):
    run_id: str
    stage: RouteStage
    rows: list[AccessResponse]
    total: int
    page: int
    page_size: int


class RegionalFacilityPageResponse(BaseModel):
    run_id: str
    facilities: list[FacilityResponse]
    total: int
    page: int
    page_size: int


class RegionalPointDetailResponse(BaseModel):
    row: AccessResponse
    facility: FacilityResponse | None


class RegionalMapCellResponse(BaseModel):
    id: str
    latitude: float
    longitude: float
    references: int
    measured: int
    minimum: float | None
    maximum: float | None
    origin_id: str | None
    bounds: tuple[float, float, float, float]


class RegionalFacilityCellResponse(BaseModel):
    id: str
    latitude: float
    longitude: float
    facilities: int
    facility_id: str | None
    bounds: tuple[float, float, float, float]


class RegionalMapViewResponse(BaseModel):
    run_id: str
    stage: RouteStage
    unit: str
    cells: list[RegionalMapCellResponse]
    viewport_references: int
    facilities: list[RegionalFacilityCellResponse]
    viewport_facilities: int
