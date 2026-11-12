import json
from dataclasses import asdict, replace
from math import isfinite

from app.usecase.traffic import TrafficJob, TrafficMetrics


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
    for row in result["alternatives"]:
        row.pop("roads")
        row.pop("vehicle_hours_saved")
        row["after"] = mobility(row["after"])
        if row["kind"] != "connection" or row["housing_clearance"] is True:
            visible.append(row)
    result["alternatives"] = visible
    if result["baseline"]:
        result["baseline"] = mobility(result["baseline"])
    return result


def mobility(values: dict[str, object]) -> dict[str, object]:
    return {key: values[key] for key in ["mean_trip_minutes", "overloaded_edges", "unserved_vehicles"]}
