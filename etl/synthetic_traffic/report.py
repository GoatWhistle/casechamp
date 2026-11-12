import json
from dataclasses import asdict
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
from synthetic_traffic.assignment import Assignment
from synthetic_traffic.incremental import evaluate_incremental, prepare_incremental
from synthetic_traffic.model import Network, Trip
from synthetic_traffic.projects import apply_project


def summary(result: Assignment, duration: float) -> dict:
    return {
        "vehicle_hours": result.vehicle_hours_per_hour * duration,
        "unserved_vehicles": result.unserved_vehicles_per_hour * duration,
        "overloaded_directed_edges": int((result.ratio > 1).sum()),
        "maximum_demand_capacity_ratio": float(result.ratio.max()),
        "relative_gap": result.relative_gap,
        "iterations": result.iterations,
        "converged": result.converged,
    }


def compare(
    network: Network,
    trips: list[Trip],
    projects: list[dict],
    destination: Path,
    duration: float,
    iterations: int,
    tolerance: float,
    metadata: dict,
    multipliers: list[float],
) -> dict:
    if destination.exists():
        raise ValueError("Result output exists; choose a new directory")
    if not np.isfinite(duration) or not 0 < duration <= 24:
        raise ValueError("Use a declared period in (0,24] hours")
    if not multipliers or any(not np.isfinite(v) or v <= 0 for v in multipliers):
        raise ValueError("Demand multipliers must be finite and positive")
    variants = [
        (str(index), project, apply_project(network, project))
        for index, project in enumerate(projects)
    ]
    destination.mkdir(parents=True)
    matrix = [asdict(trip) for trip in trips]
    canonical = json.dumps(
        matrix, sort_keys=True, separators=(",", ":"), allow_nan=False
    )
    (destination / "demand.json").write_text(canonical)
    report = {
        "method": "synthetic_passenger_od_static_msa_v1",
        "status": "running",
        "multipliers": multipliers,
        "project_count": len(projects),
        "observed_traffic": False,
        "created_at": datetime.now(UTC).isoformat(),
        "demand_sha256": sha256(canonical.encode()).hexdigest(),
        "duration_hours": duration,
        "metadata": metadata,
        "cases": [],
        "limits": [
            "Population attractiveness proxy; no observed jobs or freight demand",
            "Static assignment: overload demand is not completed throughput",
            "No network queue lengths, spillback or intersection controls",
            "New connections need independent buildability checks",
            "Coarse zones omit intrazonal routing; no induced demand",
        ],
    }
    for multiplier in multipliers:
        demand = [
            Trip(t.origin, t.destination, t.vehicles_per_hour * multiplier)
            for t in trips
        ]
        print(f"Assigning baseline, demand x{multiplier}", flush=True)
        cache = prepare_incremental(network, demand, iterations, tolerance)
        baseline = cache.assignment
        baseline_file = f"baseline-flows-{multiplier}.parquet"
        pq.write_table(
            pa.table(
                {
                    "way_id": network.way_id,
                    "source_node": network.raw_nodes[network.source],
                    "target_node": network.raw_nodes[network.target],
                    "flow": baseline.flow,
                    "hours": baseline.hours,
                    "demand_capacity_ratio": baseline.ratio,
                }
            ),
            destination / baseline_file,
        )
        case = {
            "multiplier": multiplier,
            "baseline": {**summary(baseline, duration), "edge_flows": baseline_file},
            "projects": [],
        }
        for name, project, changed in variants:
            print(f"Assigning project {name}, demand x{multiplier}", flush=True)
            result = evaluate_incremental(cache, changed, iterations, tolerance)
            values = summary(result, duration)
            comparable = (
                baseline.converged
                and result.converged
                and all(
                    (a is None) == (b is None)
                    for a, b in zip(baseline.od_hours, result.od_hours, strict=True)
                )
            )
            values.update(
                project=project,
                vehicle_hours_saved=(
                    baseline.vehicle_hours_per_hour - result.vehicle_hours_per_hour
                )
                * duration
                if comparable
                else None,
                unserved_vehicles_reduction=(
                    baseline.unserved_vehicles_per_hour
                    - result.unserved_vehicles_per_hour
                )
                * duration,
                comparison_status="converged_same_served_demand"
                if comparable
                else "inspect_convergence_and_unserved_demand",
            )
            lookup = {
                (int(a), int(b), int(w)): i
                for i, (a, b, w) in enumerate(
                    zip(network.source, network.target, network.way_id, strict=True)
                )
            }
            positions = [
                lookup.get((int(a), int(b), int(w)))
                for a, b, w in zip(
                    changed.source, changed.target, changed.way_id, strict=True
                )
            ]
            before_flow = np.array(
                [baseline.flow[i] if i is not None else 0 for i in positions]
            )
            before_ratio = np.array(
                [baseline.ratio[i] if i is not None else np.nan for i in positions]
            )
            before_hours = np.array(
                [baseline.hours[i] if i is not None else np.nan for i in positions]
            )
            table = pa.table(
                {
                    "way_id": changed.way_id,
                    "source_node": changed.raw_nodes[changed.source],
                    "target_node": changed.raw_nodes[changed.target],
                    "flow_before": before_flow,
                    "flow_after": result.flow,
                    "flow_change": result.flow - before_flow,
                    "ratio_before": pa.array(before_ratio, from_pandas=True),
                    "hours_before": pa.array(before_hours, from_pandas=True),
                    "demand_capacity_ratio": result.ratio,
                    "hours_after": result.hours,
                }
            )
            file_name = f"flows-{multiplier}-{name}.parquet"
            pq.write_table(table, destination / file_name)
            values["edge_flows"] = file_name
            case["projects"].append(values)
        report["cases"].append(case)
        (destination / "report.json").write_text(
            json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)
        )
    report["status"] = "complete"
    (destination / "report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)
    )
    return report
