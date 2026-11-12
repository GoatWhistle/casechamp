from dataclasses import asdict
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from app.domain.normative.index import IndexValue
from app.usecase.municipal_indices import MunicipalIndexQueries


class MunicipalMetricResponse(BaseModel):
    key: str
    value: float | None
    status: str
    reason: str | None
    unit: str
    population: int
    measured_population: int
    settlements: int
    measured_settlements: int
    population_coverage: float | None


class MunicipalNormativeResponse(BaseModel):
    criterion_id: str
    value: float | None
    status: str
    reason: str | None
    basis_kind: str
    qualification: str
    legal_compliance_confirmed: bool
    unit: str | None
    mode: str | None
    thresholds: tuple[float, ...]
    values: tuple[IndexValue, ...]
    mean_travel: float | None
    measured_points: int
    reference_points: int
    facilities: int
    model_revision: str | None
    definition_sha256: str | None
    source_urls: tuple[str, ...]
    origin_kind: str


class MunicipalityIndicesResponse(BaseModel):
    region_id: str
    municipality_id: str
    name: str
    season: str
    connectivity: MunicipalMetricResponse
    region_connectivity: MunicipalMetricResponse
    metrics: list[MunicipalMetricResponse]
    normative: list[MunicipalNormativeResponse]
    method: str
    model_version: str | None
    artifact_version: str | None
    source_table: str
    computed_at: str
    boundary_source_url: str
    boundary_source_sha256: str


def build_municipal_indices_router(queries: MunicipalIndexQueries) -> APIRouter:
    router = APIRouter(tags=["municipalities"])

    @router.get("/regions/{region_id}/municipalities/{municipality_id}/indices")
    def get_indices(
        region_id: str,
        municipality_id: str,
        season: Literal["road", "summer", "winter"] = "road",
    ) -> MunicipalityIndicesResponse:
        return MunicipalityIndicesResponse(
            **asdict(queries.run(region_id, municipality_id, season))
        )

    return router
