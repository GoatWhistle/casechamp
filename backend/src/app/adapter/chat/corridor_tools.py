import json
from dataclasses import asdict

from pydantic_ai import ModelRetry, RunContext

from app.adapter.chat.artifacts import ChatRun
from app.domain.errors import DomainError, InvalidQuery
from app.usecase.chat import ChatEvent
from app.usecase.chat_map import ChatMapCommand
from app.usecase.road_corridor import CorridorCalculation, RoadCorridor, RoadCorridors
from app.usecase.road_geometry import RoadGeometry


class CorridorTools:
    def __init__(self, corridors: RoadCorridors) -> None:
        self.corridors = corridors

    def resolve_road_corridor(
        self, ctx: RunContext[ChatRun], road_name: str, origin: str, destination: str
    ) -> str:
        try:
            corridor = self.corridors.resolve(road_name, origin, destination)
            self.show(ctx, corridor)
            result = asdict(corridor)
            result.pop("lines")
            result.pop("way_ids")
            result["way_count"] = len(corridor.way_ids)
            result["length_method"] = "sum_of_whole_way_lengths_including_parallel_carriageways"
            return json.dumps(result, ensure_ascii=False)
        except InvalidQuery as error:
            return json.dumps(
                {"status": "unresolved", "code": error.code, "message": error.message},
                ensure_ascii=False,
            )
        except DomainError as error:
            raise ModelRetry(error.message) from error

    def close_road_corridor(self, ctx: RunContext[ChatRun], corridor_ids: list[str]) -> str:
        try:
            jobs = self.corridors.close(corridor_ids)
            ctx.deps.pending.append(
                ChatEvent(
                    "calculation",
                    calculation=CorridorCalculation(
                        self.corridors.combined(corridor_ids), [j.id for j in jobs]
                    ),
                )
            )
            return json.dumps(
                [
                    {
                        "id": j.id,
                        "region": j.region,
                        "status": j.status,
                        "changed_ways": len(j.changes),
                    }
                    for j in jobs
                ],
                ensure_ascii=False,
            )
        except DomainError as error:
            raise ModelRetry(error.message) from error

    def resolve_road_route(self, ctx: RunContext[ChatRun], origin: str, destination: str) -> str:
        try:
            route = self.corridors.resolve_route(origin, destination)
            self.show(ctx, route.corridor)
            result = asdict(route.corridor)
            result.pop("lines")
            result.pop("way_ids")
            result["way_count"] = len(route.corridor.way_ids)
            result["travel_hours"] = route.travel_hours
            result["routing_method"] = route.routing_method
            result["length_method"] = "sum_of_whole_way_lengths_not_exact_trip_distance"
            return json.dumps(result, ensure_ascii=False)
        except InvalidQuery as error:
            return json.dumps(
                {"status": "unresolved", "message": error.message}, ensure_ascii=False
            )
        except DomainError as error:
            raise ModelRetry(error.message) from error

    def show(self, ctx: RunContext[ChatRun], corridor: RoadCorridor) -> None:
        ctx.deps.pending.append(
            ChatEvent(
                "map",
                map=ChatMapCommand(
                    "focus_road",
                    (),
                    road=RoadGeometry(
                        [
                            corridor.road_ref
                            if corridor.origin == corridor.destination
                            else f"{corridor.origin}, {corridor.destination}"
                        ],
                        corridor.length_km,
                        corridor.lines,
                    ),
                ),
            )
        )
