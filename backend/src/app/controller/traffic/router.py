from dataclasses import replace

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.domain.errors import DataUnavailable
from app.usecase.traffic import TrafficJob, TrafficPort, TrafficScope


class TrafficInput(BaseModel):
    places: list[str] = Field(default_factory=list, max_length=2)
    region: str = Field(default="", max_length=128)
    bounds: list[float] = Field(default_factory=list, max_length=4)
    demand_multiplier: float = Field(default=1, ge=0.1, le=3)
    pair_flow: float = Field(default=1000, gt=0, le=10000)
    max_projects: int = Field(default=3, ge=1, le=3)


def build_traffic_router(traffic: TrafficPort | None) -> APIRouter:
    router = APIRouter(prefix="/traffic-jobs", tags=["synthetic traffic"])

    def available() -> TrafficPort:
        if traffic is None:
            raise DataUnavailable("Traffic calculations require GRAPH_DIR and housing storage")
        return traffic

    @router.post("", response_model=TrafficJob)
    def submit(body: TrafficInput) -> TrafficJob:
        return available().submit(TrafficScope(**body.model_dump()))

    @router.get("", response_model=list[TrafficJob])
    def recent() -> list[TrafficJob]:
        return [replace(job, zones=[], roads=[], alternatives=[]) for job in available().recent()]

    @router.get("/{job_id}", response_model=TrafficJob)
    def get(job_id: str) -> TrafficJob:
        return available().get(job_id)

    @router.post("/{job_id}/cancel", response_model=TrafficJob)
    def cancel(job_id: str) -> TrafficJob:
        return available().cancel(job_id)

    return router
