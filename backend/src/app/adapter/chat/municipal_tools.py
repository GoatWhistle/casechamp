import json
from dataclasses import asdict
from typing import Literal

from pydantic_ai import Agent, ModelRetry, RunContext

from app.adapter.chat.artifacts import ChatRun
from app.adapter.chat.traffic_tools import traffic_event
from app.domain.errors import DomainError
from app.usecase.chat import ChatEvent
from app.usecase.chat_map import ChatMapCommand, MunicipalAccessMapTarget
from app.usecase.municipal_access import MunicipalAccessQueries
from app.usecase.municipal_brief import municipal_brief
from app.usecase.municipal_indices import MunicipalIndexQueries
from app.usecase.municipal_overview import municipal_overview
from app.usecase.municipal_scenarios import MunicipalScenarioRequest, MunicipalScenarios
from app.usecase.transit_brief import transit_brief
from app.usecase.transit_map import transit_map_target
from app.usecase.transit_queries import TransitQueries


class MunicipalTools:
    def __init__(self, indices: MunicipalIndexQueries, scenarios: MunicipalScenarios | None, access: MunicipalAccessQueries | None = None, transit: TransitQueries | None = None) -> None:
        self.indices = indices
        self.scenarios = scenarios
        self.access = access
        self.transit = transit

    def register(self, agent: Agent[ChatRun, str]) -> None:
        agent.tool(sequential=True, description=(
            "transit reads published bus coverage; journey combines measured walking and saved daily schedules, "
            "using returned residential origin_id/facility_id and source-clock departure_seconds (0..86399). "
            "Current journey scope uses within-region segments; missing data is not isolation. "
            "Never claim current service operation, admission or full coverage. "
            "Inspect municipal accessibility and saved road load, or evaluate +1 lane/closure. "
            "overview returns municipality IDs ranked by lowest city connectivity, or by confirmed "
            "service deficit when criterion_id is set. Unknown travel is separate; deficit intervals "
            "describe reference points, not residents. season selects connectivity only. baseline reads "
            "saved traffic and road IDs. capacity_eligible marks a supported lane-addition scenario, "
            "not construction permission; inspect capacity_reason for unsupported roads. "
            "baseline with way_ids returns visible directed segments and reverse_edge_index. "
            "start requires returned baseline_id and selected road IDs. lane_closure requires "
            "exactly one returned edge_index in edge_indices; the last lane closes that direction. "
            "A local full closure uses both segment directions. Shared lanes do not support "
            "directional lane closure. Original saved indices remain unchanged. "
            "access returns saved deficit points, facilities, P90 and worst-decile mean; criterion_id "
            "selects N01–N09, threshold uses returned unit; deficit_only=false lists the most remote "
            "points even when within threshold. Unreachable points are separate from P90. "
            "status/cancel use returned calculation_id. Traffic is synthetic; report lost demand "
            "separately and retain negative effects. Current traffic result covers the baseline "
            "network, not automatically only the selected municipality. Never claim school "
            "walking accessibility improved from road widening. Municipal N01/N02 describe "
            "travel to known medical objects at two thresholds; cardiology specialty and admission "
            "are unverified. Do not describe a nearby FAP or clinic as verified cardiology access."
        ))(self.municipal_analysis)

    def municipal_analysis(
        self,
        ctx: RunContext[ChatRun],
        action: Literal["overview", "indices", "baseline", "start", "status", "cancel", "access", "transit", "journey"],
        region_id: str = "",
        municipality_id: str = "",
        baseline_id: str = "",
        calculation_id: str = "",
        change: Literal["capacity", "closure", "lane_closure"] = "capacity",
        way_ids: list[int] | None = None,
        edge_indices: list[int] | None = None,
        criterion_id: str = "",
        threshold: float | None = None,
        deficit_only: bool = True,
        offset: int = 0,
        limit: int = 10,
        season: Literal["road", "summer", "winter"] = "road",
        origin_id: str = "",
        facility_id: str = "",
        departure_seconds: int = 28800,
    ) -> str:
        try:
            if action in {"transit", "journey"}:
                if self.transit is None:
                    raise ModelRetry("Public transport calculations are unavailable")
                target = None
                if action == "journey":
                    plan = self.transit.plan(region_id, origin_id, facility_id, departure_seconds)
                    reply = transit_brief(plan)
                    target = transit_map_target(region_id, plan)
                else:
                    reply = asdict(self.transit.coverage(region_id))
                ctx.deps.pending.append(ChatEvent("map", map=ChatMapCommand("focus", (region_id,), transit=target)))
                return json.dumps(reply, ensure_ascii=False)
            if action == "overview":
                result = municipal_overview(region_id, self.indices.municipalities, self.indices.repository,
                                            criterion_id or None, self.indices.services.published if self.indices.services else None, season,
                                            self.indices.services.published_overview if self.indices.services else None)
                return json.dumps(asdict(result), ensure_ascii=False)
            if action == "indices":
                return json.dumps(asdict(self.indices.run(region_id, municipality_id, season)), ensure_ascii=False)
            if action == "access":
                if self.access is None:
                    raise ModelRetry("Municipal accessibility detail is unavailable")
                detail = self.access.run(region_id, municipality_id, criterion_id, threshold,
                                         deficit_only=deficit_only, offset=offset, limit=limit)
                ctx.deps.pending.append(ChatEvent("map", map=ChatMapCommand(
                    "focus", (region_id,), municipal_access=MunicipalAccessMapTarget(
                        region_id, municipality_id, criterion_id, detail.threshold, deficit_only,
                    ),
                )))
                return json.dumps(asdict(detail), ensure_ascii=False)
            if self.scenarios is None:
                raise ModelRetry("Municipal traffic calculations are unavailable")
            if action == "baseline":
                baseline = self.scenarios.baseline(region_id, municipality_id)
                ctx.deps.pending.append(ChatEvent("traffic", traffic=baseline.view))
                record = asdict(baseline)
                record.pop("roads")
                record.pop("view")
                if way_ids:
                    segments = [asdict(road) for road in baseline.roads if road.way_id in way_ids]
                    record["segments"] = segments[:20]
                    record["visible_segment_count"] = len(segments)
                    record["segment_scope"] = "published_load_overlay_only"

                return json.dumps(record, ensure_ascii=False)
            if action == "start":
                job = self.scenarios.submit(MunicipalScenarioRequest(
                    baseline_id, region_id, municipality_id, change, way_ids or [], edge_indices or []
                ))
            elif action == "cancel":
                job = self.scenarios.cancel(calculation_id)
            else:
                job = self.scenarios.get(calculation_id)
            ctx.deps.pending.append(traffic_event(job))
            return json.dumps(municipal_brief(job, self.scenarios), ensure_ascii=False)
        except DomainError as error:
            raise ModelRetry(error.message) from error
