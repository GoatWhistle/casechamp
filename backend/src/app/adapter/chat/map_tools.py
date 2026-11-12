import json
from dataclasses import asdict

from pydantic_ai import Agent, ModelRetry, RunContext

from app.adapter.chat.artifacts import ChatRun
from app.adapter.chat.atlas_requests import (
    AtlasPresentation,
    ChartPresentation,
    RoadPresentation,
    SettlementPresentation,
)
from app.domain.errors import DomainError
from app.usecase.chat import ChatEvent
from app.usecase.chat_map import ChatMap, MapAction, road_map_command
from app.usecase.regions import RegionQueries
from app.usecase.road_corridor import RoadCorridors
from app.usecase.road_geometry import RoadGeometrySource
from app.usecase.settlements import SettlementQueries


class MapTools:
    def __init__(self, regions: RegionQueries, settlements: SettlementQueries | None = None,
                 roads: RoadGeometrySource | None = None, corridors: RoadCorridors | None = None) -> None:
        self._map = ChatMap(regions, settlements)
        self._roads, self._corridors = roads, corridors

    def register(self, agent: Agent[ChatRun, str]) -> None:
        agent.tool(
            sequential=True,
            description="Present verified atlas evidence: kind=chart displays numeric columns "
            "from a returned table_id; kind=map focuses 1-30 known region IDs or resets/zooms "
            "the camera; kind=settlement focuses a known settlement_id from query_atlas places "
            "or settlements. Coordinates come from storage, not the model. Use empty region_ids "
            "for non-focus map actions. kind=road highlights and zooms to known way_ids from "
            "a ranking/viewport/context or selection_ids from find_transport; no calculation needed.",
        )(self.present_atlas)

    def present_atlas(self, ctx: RunContext[ChatRun], request: AtlasPresentation) -> str:
        if isinstance(request, ChartPresentation):
            return ctx.deps.chart(request.table_id, request.x, request.y)
        if isinstance(request, RoadPresentation):
            try:
                if self._roads is None:
                    raise ValueError("Road map focus is unavailable")
                ids = list(request.way_ids)
                if request.selection_ids and self._corridors is None:
                    raise ValueError("Road selections are unavailable")
                for key in request.selection_ids:
                    if self._corridors is not None:
                        ids.extend(self._corridors.get(key).way_ids)
                command = road_map_command(self._roads, ids)
            except (ValueError, DomainError) as error:
                raise ModelRetry(str(error)) from error
            ctx.deps.pending.append(ChatEvent("map", map=command))
            return json.dumps({"action": command.action, "road_names": command.road.names if command.road else [],
                               "length_km": command.road.length_km if command.road else 0}, ensure_ascii=False)
        if isinstance(request, SettlementPresentation):
            try:
                command = self._map.settlement(request.settlement_id)
            except (ValueError, DomainError) as error:
                raise ModelRetry(str(error)) from error
            ctx.deps.pending.append(ChatEvent("map", map=command))
            return json.dumps(asdict(command), ensure_ascii=False)
        return self.control_map(ctx, request.action, request.region_ids)

    def control_map(
        self, ctx: RunContext[ChatRun], action: MapAction, region_ids: list[str]
    ) -> str:
        try:
            command = self._map.command(action, region_ids)
        except ValueError as error:
            raise ModelRetry(str(error)) from error
        ctx.deps.pending.append(ChatEvent("map", map=command))
        return json.dumps(asdict(command))
