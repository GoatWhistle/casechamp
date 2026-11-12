import json
from dataclasses import asdict

from pydantic_ai import Agent, ModelRetry, RunContext

from app.adapter.chat.artifacts import ChatRun
from app.adapter.chat.atlas_requests import (
    AtlasQuery,
    LinksQuery,
    PlacesQuery,
    ReferenceQuery,
    RegionsQuery,
    SettlementsQuery,
)
from app.adapter.chat.calculation_tools import CalculationTools
from app.adapter.chat.map_tools import MapTools
from app.usecase.chat_artifacts import (
    ChatCell,
    ChatColumn,
    ChatComparisons,
    ChatTable,
    ComparisonMetric,
)
from app.usecase.links import LinkQueries
from app.usecase.reference import ReferenceQueries
from app.usecase.regions import RegionQueries
from app.usecase.road_corridor import RoadCorridors
from app.usecase.road_geometry import RoadGeometrySource
from app.usecase.search import Search
from app.usecase.settlements import SettlementQueries, SettlementQuery


class AtlasTools:
    def __init__(
        self,
        regions: RegionQueries,
        links: LinkQueries,
        settlements: SettlementQueries,
        search: Search,
        references: ReferenceQueries,
        calculations: CalculationTools,
        roads: RoadGeometrySource | None = None,
        corridors: RoadCorridors | None = None,
    ) -> None:
        self._calculations = calculations
        self._map = MapTools(regions, settlements, roads, corridors)
        self._regions = regions
        self._comparisons = ChatComparisons(regions)
        self._links = links
        self._settlements = settlements
        self._search = search
        self._references = references

    def register(self, agent: Agent[ChatRun, str]) -> None:
        self._map.register(agent)
        self._calculations.register(agent)
        agent.tool(
            sequential=True,
            description="Read atlas evidence. Choose request.kind: places for identifiers; "
            "regions for values (supply metric for a sorted comparison table); settlements; "
            "links for the sourced catalog; sources; capabilities for available calculations "
            "and active model; sensitivity for a uniform-time experiment, not a project forecast.",
        )(self.query_atlas)

    def query_atlas(self, ctx: RunContext[ChatRun], request: AtlasQuery) -> str:
        if isinstance(request, PlacesQuery):
            return self.search_places(ctx, request.query)
        if isinstance(request, RegionsQuery):
            if request.metric is not None:
                return self.compare_regions(
                    ctx, request.metric, request.region_ids, request.limit, request.descending
                )
            rows = json.loads(self.list_regions(ctx))
            if set(request.region_ids) - {row["id"] for row in rows}:
                raise ModelRetry("Unknown region identifiers; query places first")
            return json.dumps(
                [row for row in rows if not request.region_ids or row["id"] in request.region_ids],
                ensure_ascii=False,
            )
        if isinstance(request, SettlementsQuery):
            return self.region_settlements(ctx, request.region_id, request.query)
        if isinstance(request, LinksQuery):
            return self.region_links(ctx, request.region_id, request.offset)
        if isinstance(request, ReferenceQuery):
            return self.sources(ctx) if request.kind == "sources" else self._calculations.calculation_capabilities(ctx)
        return self._calculations.accessibility_sensitivity(ctx, request.region_id)

    def list_regions(self, ctx: RunContext[ChatRun]) -> str:
        rows = self._regions.summaries(ctx.deps.context.season, ctx.deps.context.network_mode)
        return json.dumps([asdict(row) for row in rows], ensure_ascii=False)

    def region_links(self, ctx: RunContext[ChatRun], region_id: str, offset: int = 0) -> str:
        rows = self._links.region_links(region_id, ctx.deps.context.season)
        start = max(0, offset)
        selected = rows[start : start + 30]
        values: tuple[dict[str, ChatCell], ...] = tuple(
            {
                "id": row.id,
                "origin": row.origin.name,
                "destination": row.destination.name,
                "mode": row.mode.value,
                "frequency": row.freq_per_week,
                "source_url": row.source_url,
                "source_date": row.source_date,
                "confidence": row.confidence,
                "frequency_note": row.freq_note,
                "frequency_assumed": int(row.freq_assumed),
                "season": row.season,
            }
            for row in selected
        )
        table = ChatTable(
            "",
            "links",
            (
                ChatColumn("origin"),
                ChatColumn("destination"),
                ChatColumn("mode"),
                ChatColumn("frequency", "number"),
            ),
            values,
            len(rows),
            start > 0 or len(rows) > 30,
            f"/api/v1/regions/{region_id}/links?season={ctx.deps.context.season}",
        )
        return ctx.deps.table(table)

    def region_settlements(self, ctx: RunContext[ChatRun], region_id: str, query: str = "") -> str:
        page = self._settlements.page(SettlementQuery(region_id, text=query, limit=30))
        values: tuple[dict[str, ChatCell], ...] = tuple(
            {
                "id": row.id,
                "name": row.name,
                "population": row.population,
                "companies": row.companies,
            }
            for row in page.items
        )
        return ctx.deps.table(
            ChatTable(
                "",
                "settlements",
                (
                    ChatColumn("name"),
                    ChatColumn("population", "integer"),
                    ChatColumn("companies", "integer"),
                ),
                values,
                page.total,
                page.total > len(values),
                f"/api/v1/regions/{region_id}/settlements",
            )
        )

    def search_places(self, ctx: RunContext[ChatRun], query: str) -> str:
        return json.dumps(asdict(self._search.run(query)), ensure_ascii=False)

    def sources(self, ctx: RunContext[ChatRun]) -> str:
        return json.dumps([asdict(row) for row in self._references.sources()], ensure_ascii=False)

    def compare_regions(
        self,
        ctx: RunContext[ChatRun],
        metric: ComparisonMetric,
        region_ids: list[str],
        limit: int = 8,
        descending: bool = False,
    ) -> str:
        try:
            table = self._comparisons.regions(
                ctx.deps.context.season,
                ctx.deps.context.network_mode,
                metric,
                region_ids,
                limit,
                descending,
            )
        except ValueError as error:
            raise ModelRetry(str(error)) from error
        return ctx.deps.table(table)

    def show_chart(self, ctx: RunContext[ChatRun], table_id: str, x: str, y: str) -> str:
        return ctx.deps.chart(table_id, x, y)
