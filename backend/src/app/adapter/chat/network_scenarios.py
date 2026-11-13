from dataclasses import asdict

from pydantic_ai import Agent, ModelRetry, RunContext

from app.adapter.chat.analysis_tools import AnalysisTools
from app.adapter.chat.artifacts import ChatRun
from app.adapter.chat.bridge_tools import BridgeTools
from app.adapter.chat.connectivity_tools import calculate_connectivity
from app.adapter.chat.corridor_tools import CorridorTools
from app.adapter.chat.scenario_requests import (
    AnalysisScenario,
    ConnectivityScenario,
    SelectionClosure,
    TransportScenario,
)
from app.adapter.chat.stress_tools import StressTools
from app.adapter.chat.traffic_tools import TrafficTools
from app.adapter.chat.transport_tools import TransportTools
from app.domain.errors import DomainError
from app.usecase.road_analysis import RoadAnalysis
from app.usecase.road_corridor import RoadCorridors
from app.usecase.road_graph import RoadGraph
from app.usecase.road_stress import StressPort
from app.usecase.traffic import TrafficPort
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
            description="Calculate a transport scenario. connectivity reads existing routes between "
            "selected settlements, with optional resolved closures. network edits sourced transport "
            "services for 1-6 regions, with optional appraisal for one region. close_selection combines "
            "resolved closure IDs: assessment=impact returns regional and national consequences; "
            "assessment=hansen returns the regional index. region_ids extends index coverage and "
            "parent_id extends an earlier impact scenario. road_analysis with mode=criticality "
            "identifies consequences of road loss.",
        )(self.calculate_scenario)

    def calculate_scenario(self, ctx: RunContext[ChatRun], request: TransportScenario) -> str:
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
        if isinstance(request, SelectionClosure):
            if request.assessment == "impact":
                if self.stress is None:
                    raise ModelRetry("National closure impact is unavailable")
                result = StressTools(self.stress, self.corridors, self.roads).stress_test_roads(
                    ctx, [], request.selection_ids, request.parent_id, region_ids=request.region_ids
                )
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
        return TransportTools(self.roads).recalculate_transport_links(
            ctx,
            request.region_ids,
            request.scenario,
            [LinkChange(**asdict(link)) for link in request.links],
            [],
            request.appraisal,
        )
