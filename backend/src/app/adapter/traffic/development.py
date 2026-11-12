import json
from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from time import monotonic
from typing import Any

from synthetic_traffic.candidates import generate_candidates
from synthetic_traffic.incremental import IncrementalBaseline
from synthetic_traffic.model import Network, Trip, Zone
from synthetic_traffic.objectives import build_objective
from synthetic_traffic.search import search_projects

from app.adapter.traffic.hypotheses import resolve_hypotheses
from app.adapter.traffic.index_delta import IndexDelta
from app.adapter.traffic.index_targets import index_route_targets
from app.adapter.traffic.indices import TrafficIndices
from app.adapter.traffic.proposals import proposal
from app.usecase.traffic import TrafficIndexValue, TrafficJob

GENERATION_SECONDS = 120
VERIFICATION_SECONDS = 300
INDEX_CANDIDATE_SECONDS = 60


def develop(
    job: TrafficJob,
    path: Path,
    network: Network,
    trips: list[Trip],
    zones: list[Zone],
    baseline: IncrementalBaseline,
    indices: TrafficIndices | None,
    update: Callable[[TrafficJob], None],
    checkpoint: Callable[[], None],
    geography: Path | None = None,
    workers: int = 32,
) -> TrafficJob:
    development_start = monotonic()
    evidence: dict[str, Any] = json.loads(job.provenance)
    index_cache = None
    objective = (
        build_objective(
            job.scope.objective, network, baseline.assignment, trips, job.scope.focus_bounds or None
        )
        if job.scope.objective != "connectivity"
        else None
    )
    if indices and objective is None:
        if indices.revision(evidence) != indices.data.revision:
            raise ValueError("Traffic and index graph revisions differ")
        index_cache = IndexDelta(
            indices.data, network, baseline.assignment.hours, indices.regions(job, path), checkpoint
        )
        job = replace(job, indices=index_cache.baseline)
    checkpoint()
    generation_start = monotonic()
    generation_deadline = generation_start + GENERATION_SECONDS
    job = replace(job, stage="candidates", completed=0, total=GENERATION_SECONDS)
    update(job)
    hypotheses = resolve_hypotheses(job.scope.hypotheses, path, network)
    if index_cache is not None:
        hypotheses += index_route_targets(index_cache, network, generation_deadline, checkpoint)
    candidates = generate_candidates(
        network,
        baseline.assignment.flow,
        baseline.assignment.hours,
        baseline.assignment.ratio,
        128,
        geography=geography,
        deadline=generation_deadline,
        trips=trips,
        zones=zones,
        hypotheses=hypotheses,
        check=checkpoint,
    )
    checkpoint()
    generation_seconds = monotonic() - generation_start
    verification_start = monotonic()
    deadline = verification_start + VERIFICATION_SECONDS
    values_by_network: dict[int, list[TrafficIndexValue]] = {}
    index_checks: list[dict[str, Any]] = []
    observations: list[dict[str, Any]] = []

    def observe(project: dict[str, Any], after: Any, value: float, before: float) -> None:
        observations.append({
            "schema": 1,
            "project": project,
            "objective": job.scope.objective,
            "metric": "population_weighted_selected_region_hansen"
            if index_cache else "local_accessibility_delta"
            if objective is None else "negative_transit_mean_hours"
            if job.scope.objective == "transit" else "negative_vehicle_delay_hours",
            "before": before,
            "after": value,
            "gain": value - before,
            "assignment_converged": after.converged,
            "assignment_relative_gap": after.relative_gap,
            "regional_indices": [
                {"region": row.region, "value": row.value, "population": row.population}
                for row in values_by_network.get(id(after), [])
            ],
        })

    def score(changed: Network, after: Any) -> float:
        checkpoint()
        if monotonic() >= deadline:
            raise TimeoutError("Search deadline reached")
        if objective is not None:
            return objective(changed, after)
        if index_cache is None:
            raise ValueError("A calibrated index is required for development search")
        if changed is network:
            values = index_cache.baseline
        else:
            status = "failed"
            try:
                values = index_cache.evaluate(
                    changed, after.hours, min(deadline, monotonic() + INDEX_CANDIDATE_SECONDS)
                )
                status = "verified"
            except TimeoutError:
                status = "timeout"
                raise
            finally:
                index_checks.append(
                    {**getattr(index_cache, "last_evaluation", {}), "status": status}
                )
        values_by_network[id(after)] = values
        return sum(value.value * value.population for value in values) / sum(
            value.population for value in values
        )

    def cancelled() -> bool:
        checkpoint()
        return False

    job = replace(job, stage="comparing", completed=0, total=VERIFICATION_SECONDS)
    update(job)
    report = search_projects(
        network,
        trips,
        candidates,
        baseline,
        limit=job.scope.max_projects,
        workers=workers,
        deadline=deadline,
        seconds=VERIFICATION_SECONDS,
        zones=zones,
        iterations=300,
        score=score if index_cache or objective else None,
        cancelled=cancelled,
        on_evaluated=observe,
    )
    verification_seconds = monotonic() - verification_start
    alternatives = [
        proposal(
            str(i),
            row,
            network,
            baseline.assignment,
            job.indices,
            values_by_network.get(id(row.after), []),
            indices,
        )
        for i, row in enumerate(report.results)
    ]
    if objective is not None:
        before_value = -objective(network, baseline.assignment)
        alternatives = [
            replace(
                row,
                objective_before=before_value,
                objective_after=-objective(result.network, result.after),
                objective_gain=result.index_delta,
                objective_unit="hours" if job.scope.objective == "transit" else "vehicle_hours",
            )
            for row, result in zip(alternatives, report.results, strict=True)
        ]
        evidence["objective_baseline"] = objective.metrics(network, baseline.assignment)
        evidence["objective_results"] = [
            objective.metrics(row.network, row.after) for row in report.results
        ]
    evidence.update(
        generation_seconds=generation_seconds,
        generation_limit_seconds=GENERATION_SECONDS,
        verification_seconds=verification_seconds,
        verification_limit_seconds=VERIFICATION_SECONDS,
        search_seconds=verification_seconds,
        search_limit_seconds=VERIFICATION_SECONDS,
        total_development_seconds=monotonic() - development_start,
        search_workers=workers,
        search_stop=report.stop_reason,
        evaluated_projects=report.evaluated,
        verified_projects=report.verified,
        rejected_projects=report.rejected,
        index_checks=index_checks,
        verified_observations=observations,
        search_selection={
            "deduplicated": report.deduplicated,
            "invalid_packages": report.invalid_packages,
            "distinct_projects": report.distinct_projects,
            "maximum_result_buffer": report.maximum_result_buffer,
        },
        index_timeouts=sum(row["status"] == "timeout" for row in index_checks),
        surrogate=report.surrogate_version,
        geography_status=candidates.get("geography_status"),
        capacity_screening=candidates.get("capacity_screening"),
        target_diagnostics=candidates.get("target_diagnostics"),
        target_proposals=candidates.get("target_proposals", []),
        geography_missing=candidates.get("geography_missing", []),
        checked_projects=[row.project for row in report.results],
        candidate_counts={
            key: len(value) for key, value in candidates.items() if isinstance(value, list)
        },
        objective=job.scope.objective,
        objective_metric="national_hansen_delta"
        if index_cache
        else job.scope.objective
        if objective
        else "local_accessibility_delta",
    )
    return replace(
        job,
        status="completed",
        stage="completed",
        alternatives=alternatives,
        completed=report.evaluated,
        total=report.evaluated,
        provenance=json.dumps(evidence, ensure_ascii=False),
    )
