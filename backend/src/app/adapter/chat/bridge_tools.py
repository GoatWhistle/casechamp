import json
from dataclasses import asdict

from pydantic_ai import Agent, RunContext

from app.adapter.chat.artifacts import ChatRun
from app.domain.errors import DomainError
from app.usecase.chat import ChatEvent
from app.usecase.road_corridor import CorridorCalculation, RoadCorridors


class BridgeTools:
    def __init__(self, corridors: RoadCorridors) -> None:
        self.corridors = corridors

    def register(self, agent: Agent[ChatRun, str]) -> None:
        agent.tool(
            sequential=True,
            description="Find real OSM road bridges near a named settlement, optionally qualified "
            "by region after a comma. Uses is_bridge and full stored way geometry, not road names "
            "alone. Returns candidate IDs, labels, references, coordinates and distance. Connected "
            "bridge fragments and matching parallel carriageways are grouped; unrelated bridges "
            "remain separate. name optionally filters bridge name or road reference. Default "
            "radius 20km, max50. Candidates can include overpasses; choose using returned evidence, "
            "not proximity alone. For named bridge near a village, search that village. A place "
            "name is not a bridge name. If there are concrete indistinguishable choices ask the "
            "user. Never guess IDs. Regions evaluated are those of search settlements; search "
            "from both endpoint regions for cross-region closures.",
        )(self.find_road_bridges)
        agent.tool(
            sequential=True,
            description="Close one or MORE verified bridge candidates returned by find_road_bridges "
            "in ONE combined scenario per distinct search-settlement region. Pass all selected "
            "bridge_ids at once, including parallel carriageways if returned separately. Closes "
            "only bridge-tagged OSM ways in both directions; other roads remain. Emits a live "
            "calculation card with exact geometry in chat and on map. No source data changes. "
            "Return queued job IDs; never sum individual effects or invent results. An explicit "
            "user request including 'both' authorizes the scenario without another confirmation.",
        )(self.close_road_bridges)

    def find_road_bridges(
        self, ctx: RunContext[ChatRun], near: str, radius_km: float = 20, name: str = ""
    ) -> str:
        try:
            candidates = self.corridors.bridges(near, radius_km, name)
            return json.dumps({
                "status": "found" if candidates else "not_found",
                "near": near,
                "radius_km": radius_km,
                "grouping": "connected_bridge_parts_and_parallel_endpoints_within_80m",
                "length_method": "sum_of_whole_way_lengths_including_parallel_carriageways",
                "candidates": [{
                    "bridge_id": c.corridor.id,
                    "name": c.corridor.road_ref,
                    "road_references": c.references,
                    "distance_km": round(c.distance_km, 3),
                    "length_km": round(c.corridor.length_km, 3),
                    "way_ids": c.corridor.way_ids,
                    "regions": [asdict(r) for r in c.corridor.regions],
                    "bounds": [
                        min(xy[0] for line in c.corridor.lines for xy in line),
                        min(xy[1] for line in c.corridor.lines for xy in line),
                        max(xy[0] for line in c.corridor.lines for xy in line),
                        max(xy[1] for line in c.corridor.lines for xy in line),
                    ],
                } for c in candidates],
            }, ensure_ascii=False)
        except DomainError as error:
            return json.dumps({"status": "unresolved", "code": error.code, "message": error.message}, ensure_ascii=False)

    def close_road_bridges(self, ctx: RunContext[ChatRun], bridge_ids: list[str]) -> str:
        try:
            corridor = self.corridors.combine_bridges(bridge_ids)
            jobs = self.corridors.close(corridor.id)
            ctx.deps.pending.append(ChatEvent(
                "calculation", calculation=CorridorCalculation(corridor, [job.id for job in jobs]),
            ))
            return json.dumps({
                "status": "submitted",
                "combined": True,
                "way_ids": corridor.way_ids,
                "jobs": [{"id": j.id, "region": j.region, "status": j.status} for j in jobs],
            }, ensure_ascii=False)
        except DomainError as error:
            return json.dumps({"status": "unresolved", "code": error.code, "message": error.message}, ensure_ascii=False)
