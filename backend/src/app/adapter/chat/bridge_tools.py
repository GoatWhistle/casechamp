import json
from dataclasses import asdict

from pydantic_ai import RunContext

from app.adapter.chat.artifacts import ChatRun
from app.domain.errors import DomainError
from app.usecase.chat import ChatEvent
from app.usecase.road_corridor import CorridorCalculation, RoadCorridors


class BridgeTools:
    def __init__(self, corridors: RoadCorridors) -> None:
        self.corridors = corridors

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
            jobs = self.corridors.close([corridor.id])
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
