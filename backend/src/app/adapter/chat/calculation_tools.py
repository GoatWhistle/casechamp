import json
from dataclasses import asdict

from pydantic_ai import Agent, ModelRetry, RunContext

from app.adapter.chat.analysis_tools import AnalysisTools
from app.adapter.chat.artifacts import ChatRun
from app.adapter.chat.bridge_tools import BridgeTools
from app.adapter.chat.corridor_tools import CorridorTools
from app.adapter.chat.road_tools import RoadTools
from app.adapter.chat.transport_tools import TransportTools
from app.domain.errors import DomainError
from app.usecase.chat_artifacts import ChatCell, ChatColumn, ChatTable
from app.usecase.road_analysis import RoadAnalysis
from app.usecase.road_corridor import RoadCorridors
from app.usecase.road_graph import RoadGraph
from app.usecase.sensitivity import AccessibilitySensitivity


class CalculationTools:
    def __init__(
        self,
        sensitivity: AccessibilitySensitivity,
        roads: RoadGraph | None = None,
        analysis: RoadAnalysis | None = None,
        corridors: RoadCorridors | None = None,
    ) -> None:
        self._sensitivity = sensitivity
        self._roads = roads
        self._analysis = analysis
        self._corridors = corridors

    def register(self, agent: Agent[ChatRun, str]) -> None:
        if self._corridors:
            CorridorTools(self._corridors).register(agent)
            BridgeTools(self._corridors).register(agent)
        if self._analysis:
            AnalysisTools(self._analysis).register(agent)
        if self._roads:
            RoadTools(self._roads).register(agent)
            TransportTools(self._roads).register(agent)
        agent.tool(
            sequential=True,
            description="List executable calculation capabilities for all atlas regions. Always check before promising a scenario. Check national_road_edits availability; uniform-time sensitivity is NOT a project forecast.",
        )(self.calculation_capabilities)
        agent.tool(
            sequential=True,
            description="Evaluate regional Hansen sensitivity for uniformly "
            "scaled ALL origin-to-market times: 0.5x, 1x, 2x. Uses existing half-life sums "
            "with fixed baseline normalization. NOT a road-edge recalculation, no interpolation "
            "for other percentages. Explicitly label as a hypothetical sensitivity test.",
        )(self.accessibility_sensitivity)

    def calculation_capabilities(self, ctx: RunContext[ChatRun]) -> str:
        return json.dumps(
            {
                "bridge_closures": {
                    "available": self._corridors is not None and self._roads is not None,
                    "search": "find_road_bridges",
                    "calculate": "close_road_bridges",
                    "multiple_bridges": "combined_scenario",
                    "regions": "search_settlement_regions",
                },
                "named_road_corridors": {
                    "available": self._corridors is not None and self._roads is not None,
                    "directions": "both",
                    "regions": "endpoint_and_crossed_atlas_regions",
                    "joint_closure": "close_road_corridor with all corridor_ids",
                },
                "automatic_road_analysis": {
                    "available": self._analysis is not None and self._roads is not None,
                    "batch_size": 10,
                    "network": "road",
                },
                "regional_sensitivity": {
                    "time_multipliers": [0.5, 1, 2],
                    "graph_recomputed": False,
                },
                "national_road_edits": {
                    "available": self._roads is not None,
                    "version": "data-20261107",
                    "model": "snapshot includes road and intercity rail/air",
                },
                "transport_links": {
                    "available": self._roads is not None,
                    "find": "find_transport_links",
                    "calculate": "recalculate_transport_links",
                    "intercity": "remove or add rail/air between 180 market cities",
                    "local": "remove or add seasonal air/river/ferry/winter links (summer, winter)",
                    "regions": "up to 6 atlas regions per call",
                },
                "new_connections": {
                    "available": self._roads is not None,
                    "method": "single_edge_delta",
                    "network": "road",
                    "money_method": "conditional_time_savings",
                },
            },
            ensure_ascii=False,
        )

    def accessibility_sensitivity(self, ctx: RunContext[ChatRun], region_id: str) -> str:
        try:
            result = self._sensitivity.evaluate(
                region_id, ctx.deps.context.season, ctx.deps.context.network_mode
            )
        except DomainError as error:
            raise ModelRetry(error.message) from error
        rows: tuple[dict[str, ChatCell], ...] = tuple(
            {
                "id": str(point.time_multiplier),
                "time_multiplier": point.time_multiplier,
                "hansen": point.hansen,
                "delta": point.delta,
                "relative_change": point.relative_change,
            }
            for point in result.points
        )
        table = ctx.deps.table(
            ChatTable(
                "",
                "sensitivity",
                (
                    ChatColumn("time_multiplier", "percent"),
                    ChatColumn("hansen", "number"),
                    ChatColumn("relative_change", "percent"),
                ),
                rows,
                len(rows),
                False,
                f"/api/v1/regions/{region_id}/sensitivity?season={ctx.deps.context.season}"
                f"&network_mode={ctx.deps.context.network_mode}",
            )
        )
        return json.dumps(
            {"result": asdict(result), "table": json.loads(table)}, ensure_ascii=False
        )

