from dataclasses import asdict
from typing import Annotated

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.controller.normative.router import (
    AccessResponse,
    ComparisonResponse,
    FacilityResponse,
    FireProfileInput,
    NormativeRouteResponse,
)
from app.domain.normative.fire import FireProfile
from app.domain.normative.measurement_definition import MeasurementDefinition
from app.usecase.normative.regional_measurements import RegionalMeasurements
from app.usecase.normative.route import RouteStage


class RegionalMeasurementResponse(BaseModel):
    run_id: str
    region_id: str
    region_name: str
    criterion_id: str
    category: str
    graph_revision: str
    saved_at: str
    facilities: list[FacilityResponse]
    baseline_rows: list[AccessResponse]
    rows: list[AccessResponse]
    closed_way_ids: list[int]
    comparison: ComparisonResponse
    model_revision: str
    mode: str
    unit: str
    qualification: str
    fire_profile: FireProfileInput | None = None
    measurement_definition: MeasurementDefinition


class RegionalMeasurementReceiptResponse(BaseModel):
    run_id: str
    region_id: str
    region_name: str
    criterion_id: str
    graph_revision: str
    saved_at: str
    origins: int
    measured_paths: int
    facilities: int
    mode: str
    unit: str
    qualification: str
    model_revision: str
    closed_way_ids: list[int]
    measurement_definition: MeasurementDefinition


class RegionalMeasurementInput(BaseModel):
    fire_profile: FireProfileInput | None = None
    closed_way_ids: list[Annotated[int, Field(strict=True, gt=0)]] = Field(
        default_factory=list, max_length=20
    )


def build_regional_measurements_router(queries: RegionalMeasurements) -> APIRouter:
    router = APIRouter(prefix="/normative", tags=["normative"])

    @router.get(
        "/regions/{region_id}/measurements/{criterion_id}/latest",
        response_model=RegionalMeasurementResponse | None,
    )
    def latest(region_id: str, criterion_id: str) -> object:
        result = queries.latest(region_id, criterion_id)
        return asdict(result) if result else None

    @router.post(
        "/regions/{region_id}/measurements/{criterion_id}",
        response_model=RegionalMeasurementResponse,
    )
    def calculate(region_id: str, criterion_id: str, command: RegionalMeasurementInput) -> object:
        profile = FireProfile(**command.fire_profile.model_dump()) if command.fire_profile else None
        return asdict(queries.calculate(region_id, criterion_id, command.closed_way_ids, profile))

    @router.get(
        "/regions/{region_id}/measurements/{criterion_id}/receipt",
        response_model=RegionalMeasurementReceiptResponse | None,
    )
    def latest_receipt(region_id: str, criterion_id: str) -> object:
        result = queries.latest_receipt(region_id, criterion_id)
        return asdict(result) if result else None

    @router.post(
        "/regions/{region_id}/measurements/{criterion_id}/receipt",
        response_model=RegionalMeasurementReceiptResponse,
    )
    def calculate_receipt(
        region_id: str, criterion_id: str, command: RegionalMeasurementInput
    ) -> object:
        profile = FireProfile(**command.fire_profile.model_dump()) if command.fire_profile else None
        return asdict(
            queries.calculate(region_id, criterion_id, command.closed_way_ids, profile).receipt()
        )

    @router.get(
        "/regional-measurements/{run_id}/routes/{origin_id}", response_model=NormativeRouteResponse
    )
    def route(run_id: str, origin_id: str, stage: RouteStage = "scenario") -> object:
        return asdict(queries.route(run_id, origin_id, stage))

    return router
