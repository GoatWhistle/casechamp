import json
from dataclasses import asdict, replace

from pydantic_ai import ModelRetry, RunContext

from app.adapter.chat.artifacts import ChatRun
from app.adapter.chat.road_calculation import road_calculation
from app.domain.appraisal_inputs import ProjectAssumptions
from app.domain.errors import DomainError
from app.domain.road_economics import MoneyAssumptions
from app.usecase.road_graph import RoadAddition, RoadChange, RoadGraph, RoadJob


class RoadTools:
    def __init__(self, graph: RoadGraph) -> None:
        self.graph = graph

    def read_road_graph(
        self,
        ctx: RunContext[ChatRun],
        west: float,
        south: float,
        east: float,
        north: float,
        zoom: float = 10,
    ) -> str:
        try:
            view = self.graph.view(west, south, east, north, zoom)
            result = asdict(view)
            result["segments"] = result["segments"][:60]
            result["tool_limited"] = len(view.segments) > 60
            return json.dumps(result, ensure_ascii=False)
        except DomainError as error:
            raise ModelRetry(error.message) from error

    def recalculate_road_index(
        self,
        ctx: RunContext[ChatRun],
        region_id: str,
        scenario: str,
        changes: list[RoadChange],
        appraisal: ProjectAssumptions | None = None,
    ) -> str:
        try:
            geometry = self.graph.geometry([change.way_id for change in changes])
            job = self.graph.submit(region_id, scenario, changes, appraisal=appraisal)
            ctx.deps.pending.append(road_calculation(job, geometry))
            return job_reply(job)
        except DomainError as error:
            raise ModelRetry(error.message) from error

    def road_calculation_status(self, ctx: RunContext[ChatRun], job_id: str) -> str:
        try:
            job = self.graph.job(job_id)
            if job.changes:
                geometry = self.graph.geometry([change.way_id for change in job.changes])
                ctx.deps.pending.append(road_calculation(job, geometry))
            return job_reply(job)
        except DomainError as error:
            raise ModelRetry(error.message) from error

    def recent_road_calculations(self, ctx: RunContext[ChatRun]) -> str:
        try:
            return json.dumps(
                [
                    {
                        "id": job.id,
                        "region_id": job.region_id,
                        "region": job.region,
                        "scenario": job.scenario,
                        "status": job.status,
                        "changes": [
                            {
                                key: value
                                for key, value in asdict(change).items()
                                if value is not None
                            }
                            for change in job.changes[:20]
                        ],
                        "changed_ways": len(job.changes),
                        "changes_truncated": len(job.changes) > 20,
                        "addition": asdict(job.addition) if job.addition else None,
                    }
                    for job in self.graph.recent()
                ],
                ensure_ascii=False,
            )
        except DomainError as error:
            raise ModelRetry(error.message) from error

    def find_graph_locations(
        self, ctx: RunContext[ChatRun], query: str, region_id: str | None = None
    ) -> str:
        try:
            return json.dumps(
                [asdict(p) for p in self.graph.locations(query, region_id)], ensure_ascii=False
            )
        except DomainError as error:
            raise ModelRetry(error.message) from error

    def add_graph_connection(
        self,
        ctx: RunContext[ChatRun],
        region_id: str,
        source_node: int,
        target_node: int,
        travel_hours: float,
        money: MoneyAssumptions | None = None,
        appraisal: ProjectAssumptions | None = None,
    ) -> str:
        try:
            result = self.graph.add_connection(
                region_id, RoadAddition(source_node, target_node, travel_hours), money, appraisal
            )
            return json.dumps(asdict(result), ensure_ascii=False)
        except DomainError as error:
            raise ModelRetry(error.message) from error


def job_reply(job: RoadJob) -> str:
    result = (
        replace(job.result, settlement_effects=job.result.settlement_effects[:10])
        if job.result
        else None
    )
    payload = asdict(replace(job, changes=job.changes[:20], result=result))
    payload["changed_ways"] = len(job.changes)
    payload["changes_truncated"] = len(job.changes) > 20
    payload["settlement_effects_truncated"] = bool(
        job.result and len(job.result.settlement_effects) > 10
    )
    return json.dumps(payload, ensure_ascii=False)
