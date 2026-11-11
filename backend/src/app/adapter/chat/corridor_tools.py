import json
from dataclasses import asdict

from pydantic_ai import Agent, ModelRetry, RunContext

from app.adapter.chat.artifacts import ChatRun
from app.domain.errors import DomainError, InvalidQuery
from app.usecase.chat import ChatEvent
from app.usecase.road_corridor import CorridorCalculation, RoadCorridors


class CorridorTools:
    def __init__(self, corridors: RoadCorridors) -> None:
        self.corridors = corridors

    def register(self, agent: Agent[ChatRun, str]) -> None:
        agent.tool(
            sequential=True,
            description="Resolve a named highway between two settlements or market cities (Moscow and Saint Petersburg included) from the COMPLETE graph, independent of map viewport. Road references are normalized: M-10, М10, М-10 and joint refs like М-10;А-107 are one road. Returns a server corridor ID, whole-way count, attachments and atlas regions touched (endpoint and crossed regions; federal cities themselves are not model regions). Takes the shortest path along the named road between the endpoints, bridging unnamed gaps up to 15 km, plus parallel carriageways of the same road within 0.5 km; branches elsewhere are excluded. Use this for 'close highway X between A and B'. Do not ask whether both directions or which endpoint region: default both directions and evaluate both endpoint regions. State whole-OSM-way and attachment scope briefly. Resolution errors identify genuine missing/ambiguous data; never substitute a partial viewport.",
        )(self.resolve_road_corridor)
        agent.tool(
            sequential=True,
            description="Close one or several previously resolved named-road corridors TOGETHER in both directions, leaving other ways unchanged, and queue one exact Hansen calculation per atlas region the corridors touch (endpoint regions and regions crossed). Pass ALL corridor_ids of a joint closure in ONE call, e.g. M-10 and M-11 together. User's explicit request to close the named highway authorizes this model scenario; do not ask for repeated confirmation. Returns job IDs; results take about a minute and are read with road_calculation_status. No source data is modified.",
        )(self.close_road_corridor)

    def resolve_road_corridor(
        self, ctx: RunContext[ChatRun], road_name: str, origin: str, destination: str
    ) -> str:
        try:
            corridor = self.corridors.resolve(road_name, origin, destination)
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
