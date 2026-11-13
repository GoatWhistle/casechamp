from dataclasses import asdict

from fastapi import APIRouter
from pydantic import BaseModel

from app.domain.normative.model import AccessRow, Facility
from app.usecase.municipal_access import MunicipalAccessQueries


class MunicipalAccessPointResponse(BaseModel):
    row: AccessRow
    facility: Facility | None
    deficit: bool


class MunicipalAccessResponse(BaseModel):
    region_id: str
    municipality_id: str
    criterion_id: str
    source_sha256: str
    run_id: str
    measured_at: str
    unit: str
    mode: str
    threshold: float
    reference_points: int
    measured_points: int
    unreachable_points: int
    unresolved_points: int
    deficit_points: int
    p90: float | None
    worst_decile_mean: float | None
    points: list[MunicipalAccessPointResponse]
    total: int
    offset: int
    limit: int
    legal_compliance_confirmed: bool
    percentile_basis: str


def build_municipal_access_router(queries: MunicipalAccessQueries) -> APIRouter:
    router = APIRouter(tags=["municipalities"])

    @router.get("/regions/{region_id}/municipalities/{municipality_id}/access")
    def get_access(
        region_id: str,
        municipality_id: str,
        criterion_id: str,
        threshold: float | None = None,
        deficit_only: bool = True,
        offset: int = 0,
        limit: int = 100,
    ) -> MunicipalAccessResponse:
        return MunicipalAccessResponse(**asdict(queries.run(
            region_id, municipality_id, criterion_id, threshold, deficit_only, offset, limit,
        )))

    return router
