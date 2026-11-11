from collections.abc import Callable
from time import monotonic

from app.adapter.road_graph.appraisal import AppraisalRouting
from app.adapter.road_graph.baselines import BaselineCache
from app.adapter.road_graph.data import GraphData
from app.adapter.road_graph.freight_routes import freight_routes
from app.adapter.road_graph.road_profiles import profile_changes
from app.adapter.road_graph.routing import GraphRouting
from app.domain.errors import InvalidQuery
from app.usecase.road_graph import RoadJob, RoadResult
from app.usecase.road_profile_validation import has_profile


class FullCalculation:
    def __init__(
        self,
        data: GraphData,
        routing: GraphRouting,
        cache: BaselineCache,
        baselines: dict[tuple[str, str], float],
    ) -> None:
        self.data, self.routing, self.cache, self.baselines = data, routing, cache, baselines

    def calculate(
        self,
        job: RoadJob,
        region: str,
        progress: Callable[[int], None],
        appraisal: AppraisalRouting | None,
    ) -> RoadResult:
        started = monotonic()
        key = (region, job.scenario)
        cached = self.cache.read(*key)
        if cached is not None:
            self.baselines[key] = cached
        if key not in self.baselines or appraisal is not None:
            before, _, _, _, _ = self.routing.calculate(
                region,
                job.scenario,
                [],
                progress,
                on_times=appraisal.before if appraisal else None,
            )
            rows = self.data.read("expected", {"region": region, "season": job.scenario})
            if not rows:
                raise InvalidQuery("Region is missing from the calculation snapshot")
            expected = float(rows[0][0])
            if abs(before - expected) > max(0.0001, abs(expected) * 0.00001):
                raise InvalidQuery("baseline_mismatch")
            self.baselines[key] = before
            self.cache.write(*key, before)
        if appraisal is not None:
            appraisal.freight_before = freight_routes(
                self.data, region, job.scenario, [], appraisal.project.freight
            )
        progress(180)
        before = self.baselines[key]
        after, population, settlements, changed, norm = self.routing.calculate(
            region,
            job.scenario,
            job.changes,
            lambda value: progress(180 + value),
            links=job.links,
            on_times=appraisal.after if appraisal else None,
        )
        if appraisal is not None:
            appraisal.freight_after = freight_routes(
                self.data, region, job.scenario, job.changes, appraisal.project.freight
            )
        notes: list[str] = []
        if any(has_profile(c) for c in job.changes):
            ids = [c.way_id for c in job.changes]
            _, notes = profile_changes(
                job.changes, self.data.indices_for(ids), self.data.cost_profiles(ids)
            )
        return RoadResult(
            before,
            after,
            after - before,
            (after / before - 1) * 100 if before else None,
            population,
            settlements,
            changed,
            norm,
            monotonic() - started,
            road_cost_method=self.data.road_cost_model or "legacy_speed_v1",
            road_cost_notes=notes,
        )
