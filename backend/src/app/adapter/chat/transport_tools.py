import json
from dataclasses import asdict

from pydantic_ai import ModelRetry, RunContext

from app.adapter.chat.artifacts import ChatRun
from app.adapter.chat.road_calculation import road_calculation
from app.domain.appraisal_inputs import ProjectAssumptions
from app.domain.appraisal_validation import validate_project
from app.domain.errors import DomainError
from app.usecase.road_graph import RoadChange, RoadGraph
from app.usecase.transport_links import LinkChange


class TransportTools:
    def __init__(self, graph: RoadGraph) -> None:
        self.graph = graph

    def find_transport_links(
        self,
        ctx: RunContext[ChatRun],
        network: str,
        place: str,
        scenario: str = "road",
        mode: str | None = None,
    ) -> str:
        try:
            links = self.graph.transport_links(network, scenario, place, mode)
            return json.dumps(
                {
                    "links": [asdict(link) for link in links],
                    "count": len(links),
                    "possibly_truncated": len(links) >= (60 if network == "intercity" else 80),
                    "model": asdict(self.graph.model_info()),
                    "scope": "calculation_snapshot_not_live_service_schedule",
                },
                ensure_ascii=False,
            )
        except DomainError as error:
            raise ModelRetry(error.message) from error

    def recalculate_transport_links(
        self,
        ctx: RunContext[ChatRun],
        region_ids: list[str],
        scenario: str,
        links: list[LinkChange],
        road_changes: list[RoadChange] | None = None,
        appraisal: ProjectAssumptions | None = None,
    ) -> str:
        if not 1 <= len(region_ids) <= 6 or len(set(region_ids)) != len(region_ids):
            raise ModelRetry("Pass between 1 and 6 distinct atlas region IDs")
        if appraisal is not None and len(region_ids) != 1:
            raise ModelRetry("Economic appraisal requires one region per call with its own flows")
        try:
            if appraisal is not None:
                validate_project(appraisal)
            geometry = (
                self.graph.geometry([change.way_id for change in road_changes])
                if road_changes else None
            )
            jobs = [
                self.graph.submit(
                    region, scenario, road_changes or [], links, queue=True, appraisal=appraisal
                )
                for region in region_ids
            ]
            if geometry is not None:
                for job in jobs:
                    ctx.deps.pending.append(road_calculation(job, geometry))
            return json.dumps(
                [
                    {
                        "id": job.id,
                        "region": job.region,
                        "status": job.status,
                        "links": [asdict(link) for link in job.links],
                        "road_changes": len(job.changes),
                    }
                    for job in jobs
                ],
                ensure_ascii=False,
            )
        except DomainError as error:
            raise ModelRetry(error.message) from error
