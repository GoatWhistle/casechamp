from dataclasses import asdict

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.usecase.transit_access import TransitAccessResult
from app.usecase.transit_map import TransitMapTarget, transit_map_target
from app.usecase.transit_queries import TransitCoverage, TransitPlace, TransitQueries


class TransitPlanRequest(BaseModel):
    origin_id: str = Field(min_length=1, max_length=200)
    facility_id: str = Field(min_length=1, max_length=200)
    departure_seconds: int = Field(ge=0, lt=86400)
    horizon_seconds: int = Field(default=86400, ge=1, le=172800)
    maximum_walk_metres: float = Field(default=3000., gt=0, le=10000)
    transfer_seconds: int = Field(default=300, ge=0, le=3600)


class TransitPlanResponse(BaseModel):
    coverage: TransitCoverage
    origin: TransitPlace
    destination: TransitPlace
    result: TransitAccessResult
    clock_scope: str
    map_target: TransitMapTarget


def build_transit_router(queries: TransitQueries) -> APIRouter:
    router = APIRouter()

    @router.get('/regions/{region_id}/transit', response_model=TransitCoverage)
    def coverage(region_id: str) -> TransitCoverage:
        return queries.coverage(region_id)

    @router.post('/regions/{region_id}/transit-journeys', response_model=TransitPlanResponse)
    def plan(region_id: str, request: TransitPlanRequest) -> TransitPlanResponse:
        result = queries.plan(region_id, **request.model_dump())
        return TransitPlanResponse(**asdict(result), map_target=transit_map_target(region_id, result))

    return router
