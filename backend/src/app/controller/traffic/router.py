from dataclasses import replace

from fastapi import APIRouter

from app.domain.errors import DataUnavailable
from app.usecase.traffic import TrafficJob, TrafficPort
from app.usecase.traffic_evidence import public_traffic_job


def build_traffic_router(traffic: TrafficPort | None) -> APIRouter:
    router = APIRouter(prefix="/traffic-jobs", tags=["synthetic traffic"])

    def available() -> TrafficPort:
        if traffic is None:
            raise DataUnavailable("Traffic calculations require GRAPH_DIR and housing storage")
        return traffic

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
