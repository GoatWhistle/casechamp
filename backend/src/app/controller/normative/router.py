from dataclasses import asdict
from datetime import datetime
from hashlib import sha256

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field, computed_field

from app.domain.normative.fire import FireProfile
from app.domain.normative.fire_destination import FireOriginBasis, OriginBasis
from app.domain.normative.model import AccessState, Uncertainty
from app.domain.normative.rules import Applicability, RuleId, RuleReason, RuleResult, RuleUnit
from app.usecase.normative.queries import NormativeQueries
from app.usecase.normative.route import RouteStage


class CriterionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    service: str
    act: str
    clause: str
    source_url: str
    edition_date: str
    threshold: float
    unit: str
    mode: str
    territory: str
    legal_status: str
    verification_status: str


class FacilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    service: str
    name: str
    address: str
    source_url: str
    observed_at: str
    latitude: float | None
    longitude: float | None
    coordinate_source: str | None
    coordinate_status: str
    published_on: str | None = None
    source_sha256: str | None = None
    coordinate_snapshot_sha256: str | None = None
    coordinate_snapshot_url: str | None = None


class FireDestinationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    address: str
    region: str
    latitude: float
    longitude: float
    source_url: str
    observed_at: str
    reference_status: str
    source_sha256: str | None = None


class CoverageResponse(BaseModel):
    population: int
    within: int
    exceeded: int
    unreachable: int
    unknown: int
    unknown_population_points: int
    lower_percent: float | None
    upper_percent: float | None
    not_regulated_population: int = 0
    not_applicable_population: int = 0
    not_regulated_points: int = 0
    not_applicable_points: int = 0
    excluded_unknown_population_points: int = 0


class AccessResponse(BaseModel):
    id: str
    name: str
    population: int | None
    latitude: float | None
    longitude: float | None
    facility_id: str | None
    minutes: float | None
    excess_minutes: float | None
    state: AccessState
    distance_metres: float | None = None
    uncertainty: list[Uncertainty] = Field(default_factory=list)
    routing_node: int | None = None
    approach_metres: float | None = None
    threshold_minutes: float | None = None
    territory_type: str | None = None
    territory_source_url: str | None = None
    territory_verification_status: str | None = None
    municipality_code: str | None = None
    territory_structure_source_url: str | None = None
    qualification_source_url: str | None = None
    qualification_observed_at: str | None = None
    catchment_source_url: str | None = None
    threshold_source_url: str | None = None
    travel_profile_source_url: str | None = None
    measurement_method_source_url: str | None = None
    origin_source_url: str | None = None
    origin_observed_at: str | None = None
    origin_source_sha256: str | None = None
    origin_reference_status: str | None = None
    rule_set_id: str | None = None


class FireProfileInput(BaseModel):
    speed_kmh: float = Field(gt=0, le=200, allow_inf_nan=False, strict=True)
    assumption: str = Field(min_length=8, max_length=500)


class AssessmentInput(BaseModel):
    criterion_id: str
    origin_basis: FireOriginBasis = Field(default_factory=lambda: "settlements")
    fire_profile: FireProfileInput | None = None
    closed_way_ids: list[int] = Field(default_factory=list, max_length=20)


class ComparisonResponse(BaseModel):
    unit: str
    paired_paths: int
    increased: int
    decreased: int
    unchanged: int
    lost: int
    restored: int
    unresolved: int
    mean_change: float | None
    max_increase: float | None


class RouteGeometryResponse(BaseModel):
    network_coordinates: list[tuple[float, float]]
    approaches: list[list[tuple[float, float]]]
    minutes: float | None
    distance_metres: float | None


class NormativeRouteResponse(BaseModel):
    run_id: str
    origin_id: str
    facility_id: str
    stage: RouteStage
    graph_revision: str
    model_revision: str
    geometry: RouteGeometryResponse


class RuleCheckResponse(BaseModel):
    rule_id: RuleId
    applicability: Applicability
    threshold: float | None
    unit: RuleUnit
    measurement: str
    value: float | None
    result: RuleResult
    reason: RuleReason
    source_url: str
    edition_date: str
    facts_source_url: str | None
    facts_observed_at: str | None
    candidate_thresholds: list[float]


class RuleSetResponse(BaseModel):
    id: str
    checks: list[RuleCheckResponse]


class AssessmentResponse(BaseModel):
    qualification_as_of: datetime | None = None
    origin_basis: OriginBasis = Field(default_factory=lambda: "settlements")
    criterion: CriterionResponse
    facilities: list[FacilityResponse]
    graph_revision: str
    region: str
    baseline: CoverageResponse
    scenario: CoverageResponse
    baseline_rows: list[AccessResponse]
    rows: list[AccessResponse]
    closed_way_ids: list[int]
    coverage_loss_pp: float | None
    run_id: str | None
    saved_at: datetime | None = None
    rule_sets: list[RuleSetResponse] = Field(default_factory=list)
    fire_profile: FireProfileInput | None = None
    model_revision: str = "unversioned"
    comparison: ComparisonResponse | None = None
    ignored_way_ids: list[int] = Field(default_factory=list)

    @computed_field
    def graph_fingerprint(self) -> str:
        return sha256(self.graph_revision.encode()).hexdigest()


def build_normative_router(queries: NormativeQueries) -> APIRouter:
    router = APIRouter(prefix="/normative", tags=["normative"])

    @router.get("/fire-destinations", response_model=list[FireDestinationResponse])
    def fire_destinations() -> object:
        return queries.fire_destinations()

    @router.get("/criteria", response_model=list[CriterionResponse])
    def criteria() -> object:
        return queries.catalog()

    @router.get("/criteria/{criterion_id}/facilities", response_model=list[FacilityResponse])
    def facilities(criterion_id: str) -> object:
        return queries.facilities(criterion_id)

    @router.get("/criteria/{criterion_id}/latest", response_model=AssessmentResponse | None)
    def latest(criterion_id: str) -> object:
        result = queries.latest(criterion_id)
        return asdict(result) if result is not None else None

    @router.get("/assessments/{run_id}/routes/{origin_id}", response_model=NormativeRouteResponse)
    def route(run_id: str, origin_id: str, stage: RouteStage = "scenario") -> object:
        return asdict(queries.route(run_id, origin_id, stage))

    @router.post("/assessments", response_model=AssessmentResponse)
    def assess(command: AssessmentInput) -> object:
        profile = FireProfile(**command.fire_profile.model_dump()) if command.fire_profile else None
        return asdict(
            queries.assess(
                command.criterion_id, command.closed_way_ids, profile, command.origin_basis
            )
        )

    return router
