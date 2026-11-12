import json
from dataclasses import asdict

from pydantic_ai import Agent, ModelRetry, RunContext

from app.adapter.chat.artifacts import ChatRun
from app.adapter.chat.network_jobs import NetworkJobs
from app.adapter.chat.network_scenarios import NetworkScenarios
from app.adapter.chat.network_search import NetworkSearch
from app.adapter.chat.stress_tools import StressTools
from app.domain.errors import DomainError
from app.usecase.chat_artifacts import ChatCell, ChatColumn, ChatTable
from app.usecase.road_analysis import RoadAnalysis
from app.usecase.road_corridor import RoadCorridors
from app.usecase.road_graph import RoadGraph
from app.usecase.road_stress import StressPort
from app.usecase.sensitivity import AccessibilitySensitivity
from app.usecase.traffic import TrafficPort


class CalculationTools:
    def __init__(
        self,
        sensitivity: AccessibilitySensitivity,
        roads: RoadGraph | None = None,
        analysis: RoadAnalysis | None = None,
        corridors: RoadCorridors | None = None,
        stress: StressPort | None = None,
        traffic: TrafficPort | None = None,
    ) -> None:
        self._traffic = traffic
        self._stress = stress
        self._sensitivity = sensitivity
        self._roads = roads
        self._analysis = analysis
        self._corridors = corridors

    def register(self, agent: Agent[ChatRun, str]) -> None:
        if self._stress is not None:
            StressTools(self._stress, self._corridors, self._roads).register(agent)
        NetworkSearch(self._roads, self._corridors).register(agent)
        NetworkScenarios(
            self._roads, self._corridors, self._analysis, self._stress, self._traffic
        ).register(agent)
        NetworkJobs(
            self._roads, self._analysis, self._corridors, self._stress, self._traffic
        ).register(agent)

    def calculation_capabilities(self, ctx: RunContext[ChatRun]) -> str:
        model = self._roads.model_info() if self._roads else None
        return json.dumps(
            {
                "road_development": {
                    "available": self._traffic is not None,
                    "calculate": "calculate_scenario(kind=traffic_development)",
                    "objectives": ["connectivity", "transit", "congestion"],
                    "default_objective": "connectivity",
                    "scope": "bounds, exact region/regions, or resolved places; bounds describe the surrounding network context",
                    "focus_bounds": "optional measured area for transit or congestion; use stored geographic bounds or the user's map selection",
                    "workflow": "one adaptive search returns verified proposals, objective effects and map geometry",
                    "data": "manage_calculation(kind=traffic_data)",
                },
                "settlement_connectivity": {
                    "available": self._corridors is not None,
                    "calculate": "calculate_scenario(kind=connectivity)",
                    "places": "2-12 named settlements",
                    "modes": ["all_pairs", "to_center"],
                    "closures": "joint resolved selection_ids with before/after rerouting",
                    "network": "baseline roads only, undirected",
                    "half_life_hours": 2,
                    "persisted_results": "manage_calculation(kind=status, calculation_type=connectivity)",
                    "time_cost": "manage_calculation(kind=connectivity_economics, calculation_id=...)",
                },
                "national_road_stress": {
                    "available": self._stress is not None,
                    "calculate": "calculate_scenario(kind=close_selection, assessment=impact)",
                    "includes": "regional Hansen plus national road-closure consequences",
                    "selected_ways": "stress_test_roads",
                    "inspect": "inspect_road_stress_test",
                    "route": "compare_stress_route",
                    "network": "road_only_unbounded",
                    "scope": "all_snapshot_settlements",
                },
                "bridge_closures": {
                    "available": self._corridors is not None and self._roads is not None,
                    "search": "find_transport(kind=bridges)",
                    "calculate": "calculate_scenario(kind=close_selection)",
                    "multiple_bridges": "combined_scenario",
                    "regions": "search_settlement_regions",
                },
                "named_road_corridors": {
                    "available": self._corridors is not None and self._roads is not None,
                    "directions": "both",
                    "regions": "endpoint_and_crossed_atlas_regions",
                    "joint_closure": "calculate_scenario(kind=close_selection) with all selection_ids",
                    "way_ids": "resolved internally; never enumerate corridor ways",
                },
                "endpoint_road_routes": {
                    "available": self._corridors is not None and self._roads is not None,
                    "find": "find_transport(kind=road)",
                    "method": "bidirectional_dijkstra",
                    "network": "base road graph without rail/air",
                    "road_name_required": False,
                    "close": "calculate_scenario(kind=close_selection)",
                },
                "road_criticality": {
                    "available": self._analysis is not None and self._roads is not None,
                    "calculate": "calculate_scenario(kind=road_analysis, mode=criticality)",
                    "purpose": "identify consequences of road loss; development uses road_development",
                },
                "transport_model": {
                    "available": self._roads is not None,
                    "model": asdict(model) if model else None,
                },
                "transport_links": {
                    "available": self._roads is not None,
                    "find": "find_transport(kind=services)",
                    "calculate": "calculate_scenario(kind=network)",
                    "intercity": "remove or add rail/air between 180 market cities",
                    "local": "remove or add seasonal air/river/ferry/winter links (summer, winter)",
                    "regions": "up to 6 atlas regions per call",
                    "intercity_in_road": model.intercity_in_road if model else None,
                    "one_way_or_frequency_edits": False,
                    "economic_appraisal": "one region per call with explicit appraisal inputs",
                },
                "economic_appraisal": {
                    "available": self._roads is not None,
                    "method": "conditional_flow_appraisal_v1",
                    "scope": "supplied_flows_only",
                    "inputs": "passenger/freight flows, monetary rates and project costs with provenance",
                    "outputs": "annual benefits, NPV, BCR, discounted public-benefit payback",
                    "gdp_or_revenue_forecast": False,
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
