import json
from dataclasses import asdict

from pydantic_ai import Agent, ModelRetry, RunContext

from app.adapter.chat.artifacts import ChatRun
from app.adapter.chat.atlas_requests import (
    AtlasPresentation,
    ChartPresentation,
    SettlementPresentation,
)
from app.domain.errors import DomainError
from app.usecase.chat import ChatEvent
from app.usecase.chat_map import ChatMap, MapAction
from app.usecase.regions import RegionQueries
from app.usecase.settlements import SettlementQueries


class MapTools:
    def __init__(self, regions: RegionQueries, settlements: SettlementQueries | None = None) -> None:
        self._map = ChatMap(regions, settlements)

    def register(self, agent: Agent[ChatRun, str]) -> None:
        agent.tool(
            sequential=True,
            description="Present verified atlas evidence: kind=chart displays numeric columns "
            "from a returned table_id; kind=map focuses 1-30 known region IDs or resets/zooms "
            "the camera; kind=settlement focuses a known settlement_id from query_atlas places "
            "or settlements. Coordinates come from storage, not the model. Use empty region_ids "
            "for non-focus map actions.",
        )(self.present_atlas)

    def present_atlas(self, ctx: RunContext[ChatRun], request: AtlasPresentation) -> str:
        if isinstance(request, ChartPresentation):
            return ctx.deps.chart(request.table_id, request.x, request.y)
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
