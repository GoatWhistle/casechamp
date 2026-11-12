import json
from dataclasses import asdict, replace
from math import isfinite

from app.usecase.traffic import TrafficAlternative, TrafficIndexChange, TrafficJob, TrafficMetrics


def local_times(job: TrafficJob) -> TrafficJob:
    record = json.loads(job.provenance)
    demand = float(record.get("generated_vehicles_per_hour", 0))
    return replace(
        job,
        baseline=average(job.baseline, demand) if job.baseline else None,
        alternatives=[replace(row, after=average(row.after, demand)) for row in job.alternatives],
    )


def average(value: TrafficMetrics, demand: float) -> TrafficMetrics:
    served = demand - value.unserved_vehicles
    minutes = value.vehicle_hours * 60 / served if isfinite(served) and served > 0 else None
    return replace(value, mean_trip_minutes=minutes)


def traffic_brief(job: TrafficJob) -> dict[str, object]:
    job = local_times(job)
    result = asdict(job)
    for key in ["roads", "zones", "provenance", "version"]:
        result.pop(key)
    if job.status != "completed":
        for key in ["indices", "alternatives", "baseline"]:
            result.pop(key)
        return result
    visible = []
    for proposal in job.alternatives:
        if not useful(proposal, job.baseline):
            continue
        row = asdict(proposal)
        for key in ["roads", "vehicle_hours_saved", "housing_clearance"]:
            row.pop(key)
        row["overloaded_roads"] = [
            {
                "way_id": road.way_id,
                "ratio_before": road.ratio_before,
                "ratio_after": round(road.ratio_after, 2),
                "coordinates": road.coordinates,
            }
            for road in sorted(proposal.roads, key=lambda road: -road.ratio_after)
            if road.ratio_after > 1 and road.ratio_after > (road.ratio_before or 0)
        ][:3]
        row["after"] = mobility(proposal.after)
        row["indices"] = [index_summary(value) for value in proposal.indices]
        row["length_km"] = round(proposal.length_km, 3)
        if (
            job.baseline
            and job.baseline.mean_trip_minutes is not None
            and proposal.after.mean_trip_minutes is not None
        ):
            row["time_saved_seconds"] = round(
                (job.baseline.mean_trip_minutes - proposal.after.mean_trip_minutes) * 60, 1
            )
        visible.append(row)
    result["alternatives"] = visible
    result["indices"] = [
        {"region": value.region, "value": round(value.value, 4)} for value in job.indices
    ]
    result["checked_projects"] = len(job.alternatives)
    if job.baseline:
        result["baseline"] = mobility(job.baseline)
    return result


def useful(row: TrafficAlternative, baseline: TrafficMetrics | None) -> bool:
    if baseline is None or not baseline.converged or not row.after.converged:
        return False
    if row.kind == "connection" and row.housing_clearance is not True:
        return False
    before = baseline.mean_trip_minutes if baseline else None
    after = row.after.mean_trip_minutes
    local = before is not None and after is not None and before - after >= 0.05
    return (
        (row.objective_gain is not None and row.objective_gain > 0)
        or local
        or any(value.delta >= 0.0001 for value in row.indices)
    )


def index_summary(value: TrafficIndexChange) -> dict[str, object]:
    result: dict[str, object] = {
        "region": value.region,
        "before": round(value.before, 4),
        "after": round(value.after, 4),
    }
    if abs(value.delta) < 0.0001:
        result["effect"] = "unchanged"
    else:
        result["delta"] = round(value.delta, 4)
    return result


def mobility(value: TrafficMetrics) -> dict[str, object]:
    return {
        "mean_trip_minutes": round(value.mean_trip_minutes, 1)
        if value.mean_trip_minutes is not None
        else None,
        "overloaded_edges": value.overloaded_edges,
        "unserved_vehicles": value.unserved_vehicles,
    }
