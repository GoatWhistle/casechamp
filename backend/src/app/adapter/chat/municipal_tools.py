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
from app.usecase.municipal_diagnosis import municipal_diagnosis
from app.usecase.municipal_improvement import propose_lane
from app.usecase.municipal_indices import MunicipalIndexQueries
from app.usecase.municipal_overview import municipal_overview
from app.usecase.municipal_read_cache import MunicipalReadCache
from app.usecase.municipal_road_candidates import MunicipalRoadCandidates
from app.usecase.municipal_scenarios import MunicipalScenarioRequest, MunicipalScenarios
from app.usecase.transit_brief import transit_brief
from app.usecase.transit_map import transit_map_target
from app.usecase.transit_queries import TransitQueries


class MunicipalTools:
    def __init__(self, indices: MunicipalIndexQueries, scenarios: MunicipalScenarios | None, access: MunicipalAccessQueries | None = None, transit: TransitQueries | None = None, roads: MunicipalRoadCandidates | None = None, cache: MunicipalReadCache | None = None) -> None:
        self.indices = indices
        self.scenarios = scenarios
        self.access = access
        self.transit = transit
        self.roads = roads
        self.cache = cache

    def register(self, agent: Agent[ChatRun, str]) -> None:
        agent.tool(sequential=True, description=(
            "transit reads published bus coverage; journey combines measured walking and saved daily schedules, "
            "using returned residential origin_id/facility_id and source-clock departure_seconds (0..86399). "
            "Current journey scope uses within-region segments; missing data is not isolation. "
            "Never claim current service operation, admission or full coverage. "
            "Inspect municipal accessibility and saved road load, or evaluate +1 lane/closure. "
            "improve selects one supported directed segment by saved load and starts a +1 lane scenario; "
            "use once when asked for a solution and its effects. Read status by returned calculation_id. "
            "Completed comparison lists all available before/after metrics; keep zero and negative effects. "
            "roads finds municipal candidate segments before traffic is ready; road class is not bottleneck proof. "
            "Nearby access samples are geographic associations, not confirmed routes via a segment. "
            "Corridor peak load is not the exact sampled segment load. Use returned directed_segments only. "
            "diagnose selects a candidate with lowest measured connectivity below its region and returns "
            "comparison evidence, ties and coverage. This does not prove congestion or its cause. "
            "Follow with indices and baseline for that municipality before explaining road problems. "
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
        action: Literal["improve", "roads", "diagnose", "overview", "indices", "baseline", "start", "status", "cancel", "access", "transit", "journey"],
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
            if action == "improve":
                if self.scenarios is None:
                    raise ModelRetry("Municipal traffic calculations are unavailable")
                proposal, job = propose_lane(self.scenarios, region_id, municipality_id)
                if job is not None:
                    ctx.deps.pending.append(traffic_event(job))
                return json.dumps(proposal, ensure_ascii=False)
            if action == "roads":
                if self.roads is None:
                    raise ModelRetry("Municipal road search is unavailable")
                def read_roads() -> str:
                    assert self.roads is not None
                    return json.dumps(self.roads.run(region_id, municipality_id, criterion_id or "N01", min(limit, 10)), ensure_ascii=False)
                return self.cache.read("roads", {"region": region_id, "municipality": municipality_id,
                    "criterion": criterion_id or "N01", "limit": min(limit, 10)}, read_roads) if self.cache else read_roads()
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
            if action in {"overview", "diagnose"}:
                def read_overview() -> str:
                    result = municipal_overview(region_id, self.indices.municipalities, self.indices.repository,
                                                (criterion_id or None) if action == "overview" else None, self.indices.services.published if self.indices.services else None, season,
                                                self.indices.services.published_overview if self.indices.services else None)
                    return json.dumps(municipal_diagnosis(result) if action == "diagnose" else asdict(result), ensure_ascii=False)
                return self.cache.read(action, {"region": region_id, "criterion": criterion_id,
                    "season": season}, read_overview) if self.cache else read_overview()
            if action == "indices":
                def read_indices() -> str:
                    return json.dumps(asdict(self.indices.run(region_id, municipality_id, season)), ensure_ascii=False)
                return self.cache.read("indices", {"region": region_id, "municipality": municipality_id,
                    "season": season}, read_indices) if self.cache else read_indices()
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
                record["corridor_count"] = len(baseline.corridors)
                record["corridors"] = [asdict(row) for row in baseline.corridors[:min(max(limit, 1), 20)]]
                record["corridors_truncated"] = len(record["corridors"]) < len(baseline.corridors)
                record["load_quality"] = {"converged": baseline.view.baseline.converged if baseline.view.baseline else False,
                    "relative_gap": baseline.relative_gap, "routing_scenarios_ready": baseline.view.stage != "preliminary"}
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
