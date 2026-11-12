from dataclasses import replace
from typing import Literal

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.domain.errors import DataUnavailable
from app.usecase.traffic import TrafficHypothesis, TrafficJob, TrafficPort, TrafficScope
from app.usecase.traffic_evidence import public_traffic_job


class TrafficInput(BaseModel):
    places: list[str] = Field(default_factory=list, max_length=2)
    region: str = Field(default="", max_length=128)
    regions: list[str] = Field(default_factory=list, max_length=82)
    bounds: list[float] = Field(default_factory=list, max_length=4)
    demand_multiplier: float = Field(default=1, ge=0.1, le=3)
    pair_flow: float = Field(default=1000, gt=0, le=10000)
    max_projects: int = Field(default=3, ge=1, le=3)
    objective: Literal["connectivity", "transit", "congestion"] = "connectivity"
    focus_bounds: list[float] = Field(default_factory=list, max_length=4)
    hypotheses: list[TrafficHypothesis] = Field(default_factory=list, max_length=32)


def build_traffic_router(traffic: TrafficPort | None) -> APIRouter:
    router = APIRouter(prefix="/traffic-jobs", tags=["synthetic traffic"])

    def available() -> TrafficPort:
        if traffic is None:
            raise DataUnavailable("Traffic calculations require GRAPH_DIR and housing storage")
        return traffic

    @router.post("", response_model=TrafficJob)
    def submit(body: TrafficInput) -> TrafficJob:
        values = body.model_dump()
        values["hypotheses"] = [TrafficHypothesis(**h) for h in values["hypotheses"]]
        return public_traffic_job(available().submit(TrafficScope(**values)))

    @router.get("", response_model=list[TrafficJob])
    def recent() -> list[TrafficJob]:
        return [
            replace(public_traffic_job(job), zones=[], roads=[], alternatives=[])
            for job in available().recent()
        ]

    @router.get("/{job_id}", response_model=TrafficJob)
    def get(job_id: str) -> TrafficJob:
        return public_traffic_job(available().get(job_id))

    @router.post("/{job_id}/cancel", response_model=TrafficJob)
    def cancel(job_id: str) -> TrafficJob:
        return public_traffic_job(available().cancel(job_id))

    return router
