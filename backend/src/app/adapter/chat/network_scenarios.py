import json
from dataclasses import asdict

from pydantic_ai import Agent, ModelRetry, RunContext

from app.adapter.chat.analysis_tools import AnalysisTools
from app.adapter.chat.artifacts import ChatRun
from app.adapter.chat.bridge_tools import BridgeTools
from app.adapter.chat.connectivity_tools import calculate_connectivity
from app.adapter.chat.corridor_tools import CorridorTools
from app.adapter.chat.road_tools import RoadTools
from app.adapter.chat.scenario_requests import (
    AnalysisScenario,
    ConnectionScenario,
    ConnectivityScenario,
    SelectionClosure,
    SelectionEdit,
    TransportScenario,
)
from app.adapter.chat.stress_tools import StressTools
from app.adapter.chat.traffic_requests import TrafficDevelopment
from app.adapter.chat.traffic_tools import TrafficTools
from app.adapter.chat.transport_tools import TransportTools
from app.domain.errors import DomainError
from app.usecase.road_analysis import RoadAnalysis
from app.usecase.road_corridor import RoadCorridors
from app.usecase.road_graph import RoadChange, RoadGraph
from app.usecase.road_stress import StressPort
from app.usecase.traffic import TrafficPort, TrafficScope
from app.usecase.transport_links import LinkChange


class NetworkScenarios:
    def __init__(
        self,
        roads: RoadGraph | None,
        corridors: RoadCorridors | None,
        analysis: RoadAnalysis | None,
        stress: StressPort | None = None,
        traffic: TrafficPort | None = None,
    ) -> None:
        self.roads, self.corridors, self.analysis = roads, corridors, analysis
        self.stress = stress
        self.traffic = TrafficTools(traffic)

    def register(self, agent: Agent[ChatRun, str]) -> None:
        agent.tool(
            sequential=True,
            description="Calculate a transport scenario. traffic_development builds housing-derived demand, "
            "assigns road loads and verifies bounded capacity/speed/new-link alternatives with red map progress. connectivity compares selected settlements "
            "and optional closures; traffic={} adds assumed load and queues, returning a saved ID "
            "and summary. network edits roads/services for 1-6 regions, with optional appraisal "
            "for one region. close_selection combines resolved closure IDs; assessment=impact "
            "(default) jointly starts regional Hansen and national road-only consequences; assessment=hansen "
            "requests only the regional index. Optional places and traffic={} calculate assumed detour "
            "load and queues in the same call. region_ids extends index coverage. parent_id adds to an earlier impact scenario. connection adds a "
            "bidirectional link. edit_selection changes speed on resolved selection_ids "
            "with speed_factor (1.2 = +20%), resolving all ways internally on the open base "
            "network, independently of prior closures. road_analysis searches regional improvements.",
        )(self.calculate_scenario)

    def calculate_scenario(self, ctx: RunContext[ChatRun], request: TransportScenario) -> str:
        if isinstance(request, TrafficDevelopment):
            values = asdict(request)
            values.pop("kind")
            return self.traffic.calculate(ctx, TrafficScope(**values))
        if isinstance(request, ConnectivityScenario):
            if self.corridors is None:
                raise ModelRetry("Settlement connectivity is unavailable")
            return calculate_connectivity(ctx, self.corridors, request)
        if isinstance(request, AnalysisScenario):
            if self.analysis is None:
                raise ModelRetry("Automatic road analysis is unavailable")
            return AnalysisTools(self.analysis).start_road_analysis(
                ctx, request.region_id, request.mode, request.percent
            )
        if isinstance(request, SelectionEdit):
            if self.corridors is None:
                raise ModelRetry("Resolved road edits are unavailable")
            return CorridorTools(self.corridors).edit_road_corridors(
                ctx, request.selection_ids, request.speed_factor
            )
        if isinstance(request, SelectionClosure):
            if request.assessment == "impact":
                if self.stress is None:
                    raise ModelRetry("National closure impact is unavailable")
                if request.traffic is not None and (not request.places or request.parent_id):
                    raise ModelRetry("Traffic needs explicit places and all joint selection IDs, without parent_id")
                result = StressTools(self.stress, self.corridors, self.roads).stress_test_roads(
                    ctx, [], request.selection_ids, request.parent_id, region_ids=request.region_ids
                )
                if request.traffic is not None:
                    if self.corridors is None:
                        raise ModelRetry("Traffic calculation is unavailable")
                    traffic = calculate_connectivity(ctx, self.corridors, ConnectivityScenario(
                        "connectivity", request.places, selection_ids=request.selection_ids,
                        traffic=request.traffic,
                    ))
                    payload = json.loads(result)
                    payload["traffic"] = [json.loads(traffic)]
                    return json.dumps(payload, ensure_ascii=False)
                return result
            if request.parent_id:
                raise ModelRetry("parent_id is only supported for impact assessment")
            if self.corridors is None:
                raise ModelRetry("Resolved road closures are unavailable")
            try:
                selected = [self.corridors.get(key) for key in request.selection_ids]
                if selected and all(c.scope == "osm_bridge_ways_both_directions" for c in selected):
                    return BridgeTools(self.corridors).close_road_bridges(
                        ctx, request.selection_ids
                    )
                return CorridorTools(self.corridors).close_road_corridor(ctx, request.selection_ids)
            except DomainError as error:
                raise ModelRetry(error.message) from error
        if self.roads is None:
            raise ModelRetry("Calculation graph is unavailable")
        if isinstance(request, ConnectionScenario):
            return RoadTools(self.roads).add_graph_connection(
                ctx,
                request.region_id,
                request.source_node,
                request.target_node,
                request.travel_hours,
                request.money,
                request.appraisal,
            )
        return TransportTools(self.roads).recalculate_transport_links(
            ctx,
            request.region_ids,
            request.scenario,
            [LinkChange(**asdict(link)) for link in request.links],
            [RoadChange(**asdict(change)) for change in request.road_changes],
            request.appraisal,
        )
