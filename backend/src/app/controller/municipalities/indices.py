import json
from dataclasses import asdict
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel

from app.domain.normative.index import IndexValue
from app.usecase.municipal_indices import MunicipalIndexQueries
from app.usecase.municipal_overview import municipal_overview
from app.usecase.municipal_read_cache import MunicipalReadCache
from app.usecase.municipal_service_priority import MunicipalServicePriority


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


class MunicipalOverviewItemResponse(BaseModel):
    municipality_id: str
    name: str
    connectivity: MunicipalMetricResponse
    difference_from_region: float | None
    reasons: list[str]
    service: MunicipalServicePriority | None = None


class MunicipalOverviewResponse(BaseModel):
    criterion_id: str | None = None
    season: str = "road"
    region_id: str
    items: list[MunicipalOverviewItemResponse]
    region_connectivity: MunicipalMetricResponse
    model_version: str | None
    artifact_version: str | None
    source_table: str


def build_municipal_indices_router(queries: MunicipalIndexQueries, cache: MunicipalReadCache | None = None) -> APIRouter:
    router = APIRouter(tags=["municipalities"])

    @router.get("/regions/{region_id}/municipalities/{municipality_id}/indices")
    def get_indices(
        region_id: str,
        municipality_id: str,
        season: Literal["road", "summer", "winter"] = "road",
    ) -> MunicipalityIndicesResponse:
        def calculate() -> str:
            return json.dumps(asdict(queries.run(region_id, municipality_id, season)), ensure_ascii=False)
        value = cache.read("indices", {"region": region_id, "municipality": municipality_id,
                                      "season": season}, calculate) if cache else calculate()
        return MunicipalityIndicesResponse.model_validate_json(value)

    @router.get("/regions/{region_id}/municipalities-overview")
    def get_overview(region_id: str, criterion_id: str | None = None,
                     season: Literal["road", "summer", "winter"] = "road") -> MunicipalOverviewResponse:
        return MunicipalOverviewResponse(**asdict(municipal_overview(
            region_id, queries.municipalities, queries.repository, criterion_id,
            queries.services.published if queries.services else None, season,
            queries.services.published_overview if queries.services else None,
        )))

    return router
