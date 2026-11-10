import json
from dataclasses import asdict

from pydantic_ai import Agent, ModelRetry, RunContext

from app.adapter.chat.artifacts import ChatRun
from app.domain.errors import DomainError
from app.usecase.road_graph import RoadChange, RoadGraph
from app.usecase.transport_links import LinkChange


class TransportTools:
    def __init__(self, graph: RoadGraph) -> None:
        self.graph = graph

    def register(self, agent: Agent[ChatRun, str]) -> None:
        agent.tool(
            sequential=True,
            description="List existing rail/air/water links in the calculation snapshot. "
            "network='intercity': scheduled rail and air between the 180 market cities "
            "(Moscow, Saint Petersburg and regional centres); place is a city name; hours are "
            "in-vehicle times, the model adds 1 h transfer for rail and 2.5 h for air. "
            "network='local': seasonal links between settlements (air, river, ferry, winter_road, "
            "ice_crossing, pontoon_bridge) that exist only in summer/winter scenarios; place is a "
            "settlement, point ID or region name; hours include average waiting. "
            "Use before removing links and to obtain exact endpoints.",
        )(self.find_transport_links)
        agent.tool(
            sequential=True,
            description="Start real Hansen recalculations with rail/air/water link changes, "
            "optionally together with road changes, for 1-6 atlas regions (one job each). "
            "links: action 'remove' or 'add'; network 'intercity' (mode rail|air, endpoints are "
            "market city names, target '*' removes every link of that mode from the source city, "
            "e.g. closing an airport) or 'local' (endpoints are settlement point IDs from "
            "find_transport_links/find_graph_locations). 'add' needs hours (0,72]: in-vehicle time "
            "for intercity, door-to-door including waiting for local. Removing a link absent "
            "from the scenario is an error, not a silent no-op. Use scenario 'road' for "
            "intercity rail/air (the baseline includes them) and 'summer'/'winter' for local "
            "seasonal links. Federal cities are not atlas regions: evaluate the regions whose "
            "residents use the link, e.g. Московская область for Moscow. Returns job IDs; "
            "poll with road_calculation_status. Source data is never modified.",
        )(self.recalculate_transport_links)

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
                {"links": [asdict(link) for link in links], "count": len(links)},
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
    ) -> str:
        if not 1 <= len(region_ids) <= 6 or len(set(region_ids)) != len(region_ids):
            raise ModelRetry("Pass between 1 and 6 distinct atlas region IDs")
        try:
            jobs = [
                self.graph.submit(region, scenario, road_changes or [], links, queue=True)
                for region in region_ids
            ]
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
