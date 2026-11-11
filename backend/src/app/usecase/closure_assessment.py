import json
from dataclasses import asdict, replace

from app.usecase.road_corridor import RoadCorridors
from app.usecase.road_graph import RoadGraph, RoadJob
from app.usecase.road_stress import StressJob


def closure_indices(roads: RoadGraph | None, job: StressJob) -> list[RoadJob]:
    return roads.closure_jobs(job.way_ids, job.version) if roads else []


def index_evidence(job: RoadJob) -> dict[str, object]:
    result = (
        replace(job.result, settlement_effects=job.result.settlement_effects[:10])
        if job.result
        else None
    )
    return {
        "id": job.id,
        "region_id": job.region_id,
        "region": job.region,
        "status": job.status,
        "version": job.version,
        "scenario": job.scenario,
        "metric": "regional_hansen",
        "result": asdict(result) if result else None,
        "settlement_effects_truncated": bool(
            job.result and len(job.result.settlement_effects) > 10
        ),
        "appraisal": asdict(job.appraisal_result) if job.appraisal_result else None,
    }


def closure_traffic(corridors: RoadCorridors | None, job: StressJob) -> list[dict[str, object]]:
    if corridors is None:
        return []
    results = []
    for row in json.loads(corridors.recent_connectivity()):
        if set(row["closed_way_ids"]) != set(job.way_ids):
            continue
        saved = json.loads(corridors.read_connectivity(row["calculation_id"]))
        if saved["graph_version"] != job.version or not saved.get("traffic_assumptions"):
            continue
        pairs = []
        for pair in saved["pairs"]:
            traffic = pair.get("traffic")
            if not traffic:
                continue
            pairs.append(
                {
                    "origin": pair["origin"],
                    "destination": pair["destination"],
                    "before": pair["before"],
                    "after": pair["after"],
                    "time_loss_pcu_hours": pair["time_loss_pcu_hours"],
                    "displaced_flow_pcu_h": traffic["displaced_flow_pcu_h"],
                    "unserved_flow_pcu_h": traffic["unserved_flow_pcu_h"],
                    "queue_at_end_pcu": traffic["queue_at_end_pcu"],
                    "detours": [
                        {
                            key: route[key]
                            for key in (
                                "flow_pcu_h",
                                "background_pcu_h",
                                "demand_capacity_ratio",
                                "mean_hours",
                                "queue_at_end_pcu",
                                "mean_queue_hours",
                            )
                        }
                        | {
                            "capacity_pcu_h": route["route"]["capacity_pcu_h"],
                            "free_hours": route["route"]["free_hours"],
                        }
                        for route in traffic["routes"]
                    ],
                    "scope": traffic["scope"],
                }
            )
        results.append(
            {
                "calculation_id": saved["calculation_id"],
                "assumptions": saved["traffic_assumptions"],
                "pairs": pairs,
            }
        )
    return results
