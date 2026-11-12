import json
from dataclasses import asdict

from pydantic_ai import Agent, ModelRetry, RunContext

from app.adapter.chat.analysis_tools import AnalysisTools
from app.adapter.chat.artifacts import ChatRun
from app.adapter.chat.connectivity_reply import connectivity_reply
from app.adapter.chat.road_tools import RoadTools
from app.adapter.chat.scenario_requests import (
    CalculationQuery,
    CalculationRequest,
    ComparisonTable,
    ConnectivityEconomics,
    ContinueAnalysis,
    RecentCalculations,
)
from app.adapter.chat.traffic_requests import TrafficData
from app.adapter.chat.traffic_tools import TrafficTools
from app.domain.errors import DomainError
from app.usecase.calculation_tables import CalculationTables
from app.usecase.connectivity_economics import connectivity_economics
from app.usecase.road_analysis import RoadAnalysis
from app.usecase.road_corridor import RoadCorridors
from app.usecase.road_graph import RoadGraph
from app.usecase.road_stress import StressPort
from app.usecase.traffic import TrafficPort


class NetworkJobs:
    def __init__(
        self,
        roads: RoadGraph | None,
        analysis: RoadAnalysis | None,
        corridors: RoadCorridors | None = None,
        stress: StressPort | None = None,
        traffic: TrafficPort | None = None,
    ) -> None:
        self.roads, self.analysis = roads, analysis
        self.corridors = corridors
        self.traffic = TrafficTools(traffic)
        self.tables = CalculationTables(roads, stress)

    def register(self, agent: Agent[ChatRun, str]) -> None:
        agent.tool(
            sequential=True,
            description="kind=traffic_data reads national housing provenance and runtime coverage. "
            "calculation_type=traffic reads/cancels saved traffic jobs and displays their red map. kind=table builds and displays verified comparison tables from scenario_ids/stress_ids. "
            "Choose view=indices, routes or access and optional regions. Supply IDs, never cells or numbers. "
            "Read saved results by calculation_id: status returns a summary; "
            "detail=full includes connectivity road IDs. connectivity_economics computes "
            "time cost from saved traffic and an assumed rate. recent locates a missing ID. "
            "cancel stops a job; continue_analysis resumes an explicitly requested batch.",
        )(self.manage_calculation)

    def manage_calculation(self, ctx: RunContext[ChatRun], request: CalculationRequest) -> str:
        if isinstance(request, TrafficData):
            return self.traffic.available().inventory()
        if isinstance(request, CalculationQuery) and request.calculation_type == "traffic":
            return self.traffic.inspect(ctx, request.calculation_id, request.kind == "cancel")
        if isinstance(request, ComparisonTable):
            try:
                tables = self.tables.build(
                    request.scenario_ids, request.stress_ids, request.view, request.regions
                )
                return json.dumps(
                    {
                        "tables": [json.loads(ctx.deps.table(table)) for table in tables],
                        "presentation": "Already displayed; explain the takeaway without reproducing the table.",
                    },
                    ensure_ascii=False,
                )
            except DomainError as error:
                raise ModelRetry(error.message) from error
        if isinstance(request, RecentCalculations):
            rows = (
                [
                    {
                        "id": job.id,
                        "scope": asdict(job.scope),
                        "status": job.status,
                        "stage": job.stage,
                        "indices": [asdict(value) for value in job.indices],
                    }
                    for job in self.traffic.traffic.recent()[:20]
                ]
                if self.traffic.traffic
                else []
            )
            rows += json.loads(self.corridors.recent_connectivity()) if self.corridors else []
            if self.roads is not None:
                rows += json.loads(RoadTools(self.roads).recent_road_calculations(ctx))
            return json.dumps(rows, ensure_ascii=False)
        if request.calculation_id.startswith("connectivity-"):
            if self.corridors is None:
                raise ModelRetry("Connectivity storage is unavailable")
            if request.kind not in {"status", "connectivity_economics"}:
                raise ModelRetry("Completed connectivity results are immutable; use status")
            try:
                payload = self.corridors.read_connectivity(request.calculation_id)
                if isinstance(request, ConnectivityEconomics):
                    return connectivity_economics(payload, request.value_of_pcu_hour_rub)
                if isinstance(request, CalculationQuery) and request.detail == "full":
                    return payload
                return connectivity_reply(json.loads(payload))
            except DomainError as error:
                raise ModelRetry(error.message) from error
        if isinstance(request, ConnectivityEconomics):
            raise ModelRetry("Use a saved connectivity calculation ID for this appraisal")
        if isinstance(request, ContinueAnalysis):
            if self.analysis is None:
                raise ModelRetry("Road analysis is unavailable")
            return AnalysisTools(self.analysis).control_road_analysis(
                ctx, request.calculation_id, "continue"
            )
        if not isinstance(request, RecentCalculations) and request.calculation_type == "analysis":
            if self.analysis is None:
                raise ModelRetry("Road analysis is unavailable")
            tools = AnalysisTools(self.analysis)
            if request.kind == "cancel":
                return tools.control_road_analysis(ctx, request.calculation_id, "cancel")
            return tools.read_road_analysis(ctx, request.calculation_id)
        if self.roads is None:
            raise ModelRetry("Calculation graph is unavailable")
        road_tools = RoadTools(self.roads)
        if request.kind == "cancel":
            try:
                self.roads.cancel(request.calculation_id)
            except DomainError as error:
                raise ModelRetry(error.message) from error
        return road_tools.road_calculation_status(ctx, request.calculation_id)
