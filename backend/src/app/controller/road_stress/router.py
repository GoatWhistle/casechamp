from fastapi import APIRouter, Query
from pydantic import BaseModel, Field

from app.domain.errors import DataUnavailable, InvalidQuery
from app.usecase.road_geometry import RoadGeometry
from app.usecase.road_stress import (
    StressImpact,
    StressJob,
    StressPort,
    StressRouteComparison,
    StressSummary,
)


class StressInput(BaseModel):
    way_ids: list[int] = Field(min_length=1, max_length=20000)
    parent_id: str | None = None


class StressRouteInput(BaseModel):
    origin: str = Field(min_length=1, max_length=128)
    destination: str = Field(min_length=1, max_length=128)


def build_stress_router(engine: StressPort | None) -> APIRouter:
    router = APIRouter(prefix="/road-stress-tests", tags=["road-stress"])

    def service() -> StressPort:
        if engine is None:
            raise DataUnavailable("Road stress tests are unavailable")
        return engine

    @router.post("", response_model=StressJob)
    def submit(body: StressInput) -> StressJob:
        return service().submit(body.way_ids, body.parent_id)

    @router.get("", response_model=list[StressJob])
    def recent() -> list[StressJob]:
        return service().recent()

    @router.get("/{job_id}", response_model=StressJob)
    def get(job_id: str) -> StressJob:
        return service().get(job_id)

    @router.get("/{job_id}/summary", response_model=StressSummary)
    def summary(job_id: str, region: str = "") -> StressSummary:
        return service().summary(job_id, region)

    @router.delete("/{job_id}", response_model=StressJob)
    def cancel(job_id: str) -> StressJob:
        return service().cancel(job_id)

    @router.get("/{job_id}/impacts", response_model=list[StressImpact])
    def impacts(job_id: str, region: str = "", offset: int = Query(0, ge=0),
                limit: int = Query(50, ge=1, le=200),
                west: float | None = None, south: float | None = None,
                east: float | None = None, north: float | None = None) -> list[StressImpact]:
        bounds = None
        if any(v is not None for v in (west, south, east, north)):
            if west is None or south is None or east is None or north is None:
                raise InvalidQuery("All bounds are required")
            if not -180 <= west <= east <= 180 or not -90 <= south <= north <= 90:
                raise InvalidQuery("Invalid bounds")
            bounds = (west, south, east, north)
        return service().impacts(job_id, region, offset, limit, bounds)

    @router.get("/{job_id}/geometry", response_model=RoadGeometry)
    def geometry(job_id: str) -> RoadGeometry:
        return service().geometry(job_id)

    @router.post("/{job_id}/routes", response_model=StressRouteComparison)
    def route(job_id: str, body: StressRouteInput) -> StressRouteComparison:
        return service().route(job_id, body.origin, body.destination)

    return router
