import json
from dataclasses import asdict

from pydantic_ai import Agent, ModelRetry, RunContext

from app.adapter.chat.artifacts import ChatRun
from app.adapter.chat.road_calculation import road_calculation
from app.domain.errors import DomainError
from app.usecase.chat import ChatEvent
from app.usecase.closure_assessment import closure_indices, closure_traffic, index_evidence
from app.usecase.road_corridor import RoadCorridors
from app.usecase.road_graph import RoadGraph
from app.usecase.road_stress import StressPort
from app.usecase.saved_road_closure import saved_closure_ways


class StressTools:
    def __init__(self, stress: StressPort, corridors: RoadCorridors | None,
                 roads: RoadGraph | None = None) -> None:
        self.stress, self.corridors, self.roads = stress, corridors, roads

    def register(self, agent: Agent[ChatRun, str]) -> None:
        agent.tool(sequential=True, description="Simulate road closures nationally, road only, "
                   "with regional Hansen indices and road-only consequences without a 72h cutoff. "
                   "region_ids extends index coverage; source_stress_id enriches a saved closure. "
                   "Use resolved selection IDs from find_transport "
                   "or known way IDs. source_calculation_id reuses the exact closure from a saved "
                   "regional Hansen calculation; pass empty ID lists. parent_id retains earlier closures. Population is exposure, "
                   "not observed traffic. Emits a live interactive result card.")(self.stress_test_roads)
        agent.tool(description="Read one evidence bundle: matched regional Hansen, saved traffic, region overview "
                   "and closure consequences. With region, returns delay exposure at 30/60/120 minutes, "
                   "lost nearby connections, named destinations and before/after examples. "
                   "region accepts an atlas name or ID and filters totals and examples; offset pages examples only. "
                   "Null totals mean unfinished, not zero impact.")(self.inspect_road_stress_test)
        agent.tool(description="Compare the actual fastest road path before and after a saved "
                   "closure using settlement point IDs, including route geometry and km.")(self.compare_stress_route)

    def stress_test_roads(self, ctx: RunContext[ChatRun], way_ids: list[int],
                          selection_ids: list[str], parent_id: str | None = None,
                          source_calculation_id: str | None = None,
                          source_stress_id: str | None = None,
                          region_ids: list[str] | None = None) -> str:
        try:
            if source_stress_id:
                if way_ids or selection_ids or parent_id or source_calculation_id:
                    raise ModelRetry("Choose one saved scenario or explicit closures")
                saved = self.stress.get(source_stress_id)
                if self.roads and saved.version != self.roads.model_info().version:
                    raise ModelRetry("Saved closure belongs to a different graph version")
                ids = saved.way_ids
            elif source_calculation_id:
                if way_ids or selection_ids or parent_id:
                    raise ModelRetry("Choose saved calculation or explicit closures, not both")
                if self.roads is None:
                    raise ModelRetry("Saved regional calculations are unavailable")
                ids = saved_closure_ways(self.roads, source_calculation_id)
            else:
                ids = list(way_ids or (() if selection_ids else ctx.deps.context.road_way_ids))
            if selection_ids:
                if self.corridors is None:
                    raise ModelRetry("Road selections unavailable")
                for key in selection_ids:
                    ids.extend(self.corridors.get(key).way_ids)
            job = self.stress.submit(ids, parent_id)
            regions = list(region_ids or [])
            if self.corridors:
                regions += [r.id for key in selection_ids for r in self.corridors.get(key).regions]
            if source_calculation_id and self.roads:
                regions.append(self.roads.job(source_calculation_id).region_id)
            if parent_id and self.roads:
                regions += [j.region_id for j in closure_indices(self.roads, self.stress.get(parent_id))]
            if not regions and not selection_ids and ctx.deps.context.region_id:
                regions.append(ctx.deps.context.region_id)
            indices = self.roads.submit_closure(job.way_ids, list(dict.fromkeys(regions)), job.version) if self.roads and regions else []
            if indices:
                geometry = self.stress.geometry(job.id)
                ctx.deps.pending.append(road_calculation(indices[0], geometry, [j.id for j in indices]))
            ctx.deps.pending.append(ChatEvent("stress_test", stress_test=job))
            payload = json.loads(self.reply(job.id, "", 0))
            if indices:
                payload["indices"] = [index_evidence(index) for index in indices]
                payload["index_status"] = "available"
            if source_calculation_id:
                payload["source_calculation_id"] = source_calculation_id
            return json.dumps(payload, ensure_ascii=False)
        except DomainError as error:
            raise ModelRetry(error.message) from error

    def inspect_road_stress_test(self, ctx: RunContext[ChatRun], job_id: str,
                                 region: str = "", offset: int = 0) -> str:
        try:
            job = self.stress.get(job_id)
            ctx.deps.pending.append(ChatEvent("stress_test", stress_test=job))
            return self.reply(job_id, region, max(0, offset))
        except DomainError as error:
            raise ModelRetry(error.message) from error

    def reply(self, job_id: str, region: str, offset: int) -> str:
        summary = self.stress.summary(job_id, region)
        points = self.stress.impacts(job_id, summary.region, offset, 5) if summary.totals else []
        job = self.stress.get(job_id)
        indices = closure_indices(self.roads, job)
        try:
            names = self.stress.geometry(job_id).names
        except DomainError:
            names = []
        return json.dumps({
            "road_names": names,
            "summary": asdict(summary),
            "indices": [index_evidence(index) for index in indices],
            "index_scope": "listed regions only; active atlas network and normalization, distinct from road-only consequences",
            "index_status": "available" if indices else "not_calculated",
            "traffic": closure_traffic(self.corridors, job),
            "traffic_scope": "matching saved pair scenarios among latest 20; empty means not modeled, not no congestion",
            "region_overview": [asdict(r) for r in job.regions],
            "points": [{"id": p.point.id, "name": p.point.name, "region": p.point.region,
                        "population": p.point.population, "external_isolation": p.external_isolation,
                        "lost_markets": p.lost_markets, "delay_minutes": p.delay_minutes,
                        "worst_market": p.worst_market,
                        "connections": [asdict(m) for m in p.markets[:5]],
                        "connections_truncated": len(p.markets) > 5} for p in points],
            "interpretation": {
                "network": "fixed_weights_road_only_without_72h_cutoff",
                "affected": "lost market or delay >= 1 minute to any model market",
                "isolation": "new loss of all external model markets, not proven physical isolation",
                "population": "residents of affected settlements, not road users or traffic",
                "delay": "maximum finite directional increase; unreachable paths counted separately",
                "connections": "settlement-to-market pairs, not road segments; crossing 2 hours is loss of some nearby links, not all nearby access",
                "regional_metrics": "consequences covers all stored regional impacts, not the example page",
                "delay_exposure": "cumulative thresholds: residents with any finite market delay; do not sum bands",
                "nearby_access": "connections originally within 2 hours; means use the same surviving changed connections",
                "forecast": "conditional road-network effect of this exact closure; not demand, GDP or service disruption",
                "coverage": "snapshot_points, unbound_points and preexisting_isolated_points are national",
            },
        }, ensure_ascii=False)

    def compare_stress_route(self, ctx: RunContext[ChatRun], job_id: str,
                             origin: str, destination: str) -> str:
        try:
            result = self.stress.route(job_id, origin, destination)
            ctx.deps.pending.append(ChatEvent("stress_test", stress_test=self.stress.get(job_id), stress_route=result))
            return json.dumps({"origin": result.origin.name, "destination": result.destination.name,
                               "before": {"status": result.before.status, "hours": result.before.hours, "km": result.before.km},
                               "after": {"status": result.after.status, "hours": result.after.hours, "km": result.after.km}}, ensure_ascii=False)
        except DomainError as error:
            raise ModelRetry(error.message) from error
