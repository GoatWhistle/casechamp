from dataclasses import asdict

from fastapi import APIRouter
from pydantic import BaseModel

from app.domain.normative.measurement_definition import MeasurementDefinition
from app.usecase.normative.index_map import IndexMapQueries
from app.usecase.normative.indices import RegionalIndices
from app.usecase.normative.route import RouteStage


class IndexBasisReviewResponse(BaseModel):
    reviewed_at: str
    as_of: str
    locator: str
    source_url: str
    source_sha256: str
    scope: str


class IndexThresholdIntervalResponse(BaseModel):
    minimum: float
    maximum: float
    municipality_type: str
    mode: str
    profile: str


class IndexBasisResponse(BaseModel):
    criterion_id: str
    region_id: str
    act: str
    clause: str
    edition_date: str
    source_url: str
    unit: str
    thresholds: list[float]
    definition_sha256: str
    currentness: str
    required_mode: str
    regulation: str
    review: IndexBasisReviewResponse | None
    intervals: list[IndexThresholdIntervalResponse]
    required_measurement_definition: MeasurementDefinition


class IndexValueResponse(BaseModel):
    threshold: float
    reference_points: int
    measured_points: int
    within_points: int
    unresolved_points: int
    point_share_percent: float | None
    population: int | None
    within_population: int | None
    population_share_percent: float | None


class ScenarioIndexPolicyResponse(BaseModel):
    criterion_id: str
    thresholds: list[float]
    unit: str
    mode: str
    weighting: str
    definition_sha256: str
    fire_speed_kmh: float | None


class ScenarioIndexResponse(BaseModel):
    region_id: str
    criterion_id: str
    run_id: str
    measured_at: str
    policy: ScenarioIndexPolicyResponse
    baseline: list[IndexValueResponse]
    scenario: list[IndexValueResponse]
    measurement_definition: MeasurementDefinition
    legal_compliance_confirmed: bool


class RegionalIndexResponse(BaseModel):
    region_id: str
    criterion_id: str
    run_id: str | None
    measured_at: str | None
    basis: IndexBasisResponse | None
    baseline: list[IndexValueResponse]
    scenario: list[IndexValueResponse]
    qualification: str
    weighting: str
    status: str
    legal_compliance_confirmed: bool
    measurement_definition: MeasurementDefinition
    model_index: ScenarioIndexResponse | None


class IndexMapRegionResponse(BaseModel):
    region_id: str
    region_name: str
    value_min: float | None
    value_max: float | None
    weighting: str
    status: str
    run_id: str | None
    measured_at: str | None
    threshold_min: float | None
    threshold_max: float | None
    unit: str | None
    reference_points: int | None
    measured_points: int | None
    legal_compliance_confirmed: bool
    data_source: str = "live"
    source_report: str | None = None
    source_report_sha256: str | None = None
    source_checked_at: str | None = None
    detail_available: bool = True


def build_regional_indices_router(
    queries: RegionalIndices, map_queries: IndexMapQueries
) -> APIRouter:
    router = APIRouter(prefix="/normative", tags=["normative"])

    @router.get("/regions/{region_id}/indices/{criterion_id}", response_model=RegionalIndexResponse)
    def latest(region_id: str, criterion_id: str) -> object:
        return asdict(queries.latest(region_id, criterion_id))

    @router.get("/indices/{criterion_id}/regions", response_model=list[IndexMapRegionResponse])
    def regions(criterion_id: str, stage: RouteStage = "scenario") -> object:
        return [asdict(row) for row in map_queries.regions(criterion_id, stage)]

    return router
