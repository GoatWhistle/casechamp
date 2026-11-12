import argparse
import json
import os
import subprocess
from collections import Counter
from dataclasses import asdict, replace
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path
from time import monotonic
from unittest.mock import patch

from app.adapter.road_graph.data import GraphData
from app.adapter.traffic import development
from app.adapter.traffic.hypotheses import resolve_hypotheses
from app.adapter.traffic.index_delta import IndexDelta
from app.adapter.traffic.indices import TrafficIndices
from app.adapter.traffic.visuals import metrics
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.graph_snapshot import ClickHouseGraphSnapshot
from app.usecase.traffic import TrafficHypothesis, TrafficJob, TrafficScope
from app.usecase.traffic_presentation import average, local_times
from synthetic_traffic import search as search_module
from synthetic_traffic.demand import aggregate, generate
from synthetic_traffic.geography import RasterGeography
from synthetic_traffic.housing import distribute
from synthetic_traffic.incremental import prepare_incremental
from synthetic_traffic.model import DemandParameters
from synthetic_traffic.source import load_network, load_places
from synthetic_traffic.surrogate import ARTIFACT, load_surrogate


def write(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False)
    )
    temporary.replace(path)


def fingerprint(path):
    digest = sha256()
    with path.open("rb") as source:
        while block := source.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def source_hashes(root):
    paths = [
        *root.glob("etl/synthetic_traffic/*.py"),
        *root.glob("backend/src/app/adapter/traffic/*.py"),
    ]
    paths += [
        root / "backend/src/app/usecase/traffic.py",
        root / "backend/src/app/usecase/traffic_presentation.py",
    ]
    runner = root / "work/network-development/run_hypothesis_pilot.py"
    if runner.exists():
        paths.append(runner)
    return {str(path.relative_to(root)): fingerprint(path) for path in sorted(paths)}


def reader(root):
    values = {}
    for line in (root / ".env.analytics").read_text().splitlines():
        if "=" in line and not line.lstrip().startswith("#"):
            key, value = line.removeprefix("export ").split("=", 1)
            values[key.strip()] = value.strip().strip('"').strip("'")
    values.update(
        {
            key: value
            for key, value in os.environ.items()
            if key.startswith("CLICKHOUSE_")
        }
    )
    return ClickHouseReader(
        values["CLICKHOUSE_URL"],
        values.get("CLICKHOUSE_USER", "plexus"),
        values["CLICKHOUSE_PASSWORD"],
    )


def origins(project):
    if project.get("kind") == "package":
        return sorted(
            {origin for part in project["projects"] for origin in origins(part)}
        )
    return [project.get("target_origin", project.get("origin", "existing_corridor"))]


def prepare(root, snapshot, checkpoint):
    network = load_network(snapshot)
    settlements, binding = load_places(snapshot, network)
    homes, housing = distribute(snapshot / "housing.parquet", settlements, network)
    zones, cell = aggregate(homes, network, 2, 128)
    parameters = DemandParameters()
    trips, demand = generate(network, zones, parameters)
    if not trips:
        raise ValueError("Snapshot has no generated interzonal demand")
    source = json.loads((snapshot / "source.json").read_text())
    evidence = {
        "source": source,
        "binding": binding,
        "housing": housing,
        "demand": demand,
        "parameters": asdict(parameters),
        "cell_km": cell,
        "od_pairs": len(trips),
        "generated_vehicles_per_hour": sum(trip.vehicles_per_hour for trip in trips),
        "demand_sha256": sha256(
            json.dumps([asdict(t) for t in trips], sort_keys=True).encode()
        ).hexdigest(),
        "observed_traffic": False,
    }
    baseline = prepare_incremental(network, trips, 300, 1e-3, check=checkpoint)
    if not baseline.assignment.converged:
        raise ValueError("Shared baseline did not converge; comparison cannot run")
    job = TrafficJob(
        "traffic-hypothesis-pilot",
        TrafficScope(),
        bounds=source["bounds"],
        baseline=metrics(baseline.assignment),
        provenance=json.dumps(evidence),
    )
    indices = TrafficIndices(
        GraphData(root / "data/graph_ru", ClickHouseGraphSnapshot(reader(root)))
    )
    cache = IndexDelta(
        indices.data,
        network,
        baseline.assignment.hours,
        indices.regions(job, snapshot),
        checkpoint,
    )
    return (
        network,
        zones,
        trips,
        baseline,
        replace(job, indices=cache.baseline),
        indices,
        cache,
    )


def run_arm(name, hypotheses, prepared, snapshot, frozen, output):
    network, zones, trips, baseline, job, indices, cache = prepared
    job = replace(
        job,
        id="traffic-hypothesis-" + name,
        scope=replace(job.scope, hypotheses=hypotheses),
    )
    demand = sum(trip.vehicles_per_hour for trip in trips)
    resolved = resolve_hypotheses(hypotheses, snapshot, network)
    llm_pairs = {
        tuple(sorted((row["source_node"], row["target_node"]))) for row in resolved
    }
    real_generate, real_search, real_apply = (
        development.generate_candidates,
        development.search_projects,
        search_module.apply_project,
    )
    real_evaluate = cache.evaluate
    trace = {
        "arm": name,
        "llm_input_count": len(hypotheses),
        "llm_resolved_count": len(resolved),
        "index_attempts": [],
    }
    current_project, current_indices = {}, []

    def progress(status="running"):
        verified = [
            row
            for row in trace["index_attempts"]
            if row.get("status") == "index_verified"
        ]
        base = sum(row.value * row.population for row in cache.baseline) / sum(
            row.population for row in cache.baseline
        )
        last = trace["index_attempts"][-1] if trace["index_attempts"] else {}
        value = {
            "arm": name,
            "status": status,
            "elapsed_seconds": monotonic() - arm_started,
            "index_attempts": len(trace["index_attempts"]),
            "verified": len(verified),
            "best_index_gain": max(
                [0.0] + [row["weighted_regional_index"] - base for row in verified]
            ),
            "last_attempt_status": last.get("status", "index_error"),
            "last_index_seconds": last.get("index_seconds"),
            "timing_counters": dict(getattr(cache, "last_evaluation", {})),
        }
        write(output / f"{name}-progress.json", value)
        print(json.dumps(value, ensure_ascii=False, allow_nan=False), flush=True)

    def traced_generate(*args, **kwargs):
        trace["llm_forwarded_count"] = sum(
            row.get("origin") == "agent_hypothesis"
            for row in kwargs.get("hypotheses", [])
        )
        trace["index_route_forwarded_count"] = sum(
            row.get("origin") == "index_route" for row in kwargs.get("hypotheses", [])
        )
        candidates = real_generate(*args, **kwargs)
        connections = candidates.get("connections_for_review", [])
        trace["target_diagnostics"] = candidates.get("target_diagnostics", {})
        trace["target_origin_counts"] = dict(
            Counter(
                row.get("target_origin", "automatic")
                for row in candidates.get("target_proposals", [])
            )
        )
        trace["corridor_origin_counts"] = dict(
            Counter(row.get("target_origin", "automatic") for row in connections)
        )
        trace["llm_emitted_targets"] = trace["target_origin_counts"].get(
            "agent_hypothesis", 0
        )
        trace["candidate_origin_counts"] = dict(
            Counter(
                origin
                for key in ("existing_corridor_projects", "connections_for_review")
                for project in candidates.get(key, [])
                for origin in origins(project)
            )
        )
        trace["llm_emitted_corridors"] = sum(
            row.get("target_origin") == "agent_hypothesis" for row in connections
        )
        trace["llm_pair_overlap_emitted_corridors"] = sum(
            tuple(sorted((row["source_node"], row["target_node"]))) in llm_pairs
            for row in connections
        )
        write(output / f"{name}-candidates.json", candidates)
        return candidates

    def traced_apply(changed, project):
        current_project.clear()
        current_project.update(project)
        return real_apply(changed, project)

    def traced_evaluate(changed, hours, deadline):
        values = real_evaluate(changed, hours, deadline)
        current_indices[:] = [asdict(value) for value in values]
        return values

    def traced_search(*args, **kwargs):
        real_score = kwargs["score"]

        def score(changed, after):
            if changed is network:
                return real_score(changed, after)
            record = {
                "project": dict(current_project),
                "origins": origins(current_project),
                "after": asdict(average(metrics(after), demand)),
                "same_served_od": all(
                    (a is None) == (b is None)
                    for a, b in zip(
                        baseline.assignment.od_hours, after.od_hours, strict=True
                    )
                ),
            }
            current_indices.clear()
            attempt_started = monotonic()
            try:
                value = real_score(changed, after)
                record.update(
                    status="index_verified",
                    weighted_regional_index=value,
                    regional_indices=list(current_indices),
                )
                return value
            except TimeoutError:
                record["status"] = "index_timeout"
                raise
            finally:
                record["index_seconds"] = monotonic() - attempt_started
                trace["index_attempts"].append(record)
                progress()

        kwargs["score"] = score
        with patch.object(search_module, "apply_project", traced_apply):
            return real_search(*args, **kwargs)

    arm_started = monotonic()
    try:
        with (
            patch.object(development, "IndexDelta", lambda *args, **kwargs: cache),
            patch.object(development, "generate_candidates", traced_generate),
            patch.object(development, "search_projects", traced_search),
            patch.object(cache, "evaluate", traced_evaluate),
        ):
            result = development.develop(
                job,
                snapshot,
                network,
                trips,
                zones,
                baseline,
                indices,
                lambda value: print(
                    json.dumps(
                        {
                            "arm": name,
                            "stage": value.stage,
                            "elapsed": monotonic() - arm_started,
                        }
                    ),
                    flush=True,
                ),
                lambda: None,
                frozen,
                32,
            )
        result = local_times(result)
        record = asdict(result)
        record.pop("roads", None)
        record.pop("zones", None)
        for alternative in record["alternatives"]:
            alternative.pop("roads", None)
        trace.update(
            status=result.status, job=record, evidence=json.loads(result.provenance)
        )
        trace["benefits"] = [
            {
                "id": row.id,
                "kind": row.kind,
                "regional_index_changes": [asdict(value) for value in row.indices],
                "weighted_regional_index_gain": sum(
                    value.delta * value.population for value in row.indices
                )
                / sum(value.population for value in row.indices)
                if row.indices
                else None,
                "local_mean_minutes_before": result.baseline.mean_trip_minutes
                if result.baseline
                else None,
                "local_mean_minutes_after": row.after.mean_trip_minutes,
                "vehicle_hours_saved": row.vehicle_hours_saved,
                "overloaded_edges_before": result.baseline.overloaded_edges
                if result.baseline
                else None,
                "overloaded_edges_after": row.after.overloaded_edges,
                "overload_increase": row.overload_increase,
            }
            for row in result.alternatives
        ]
    except Exception as error:  # noqa: BLE001 - preserve failed arm evidence without discarding its comparison
        trace.update(status="failed", error_type=type(error).__name__, error=str(error))
    trace["elapsed_seconds"] = monotonic() - arm_started
    trace["index_checked_project_origin_counts"] = dict(
        Counter(origin for row in trace["index_attempts"] for origin in row["origins"])
    )
    trace["origin_accounting_limit"] = (
        "Index-attempted converged projects only; solver-rejected and unfinished worker projects have no origin trace"
    )
    write(output / f"{name}-result.json", trace)
    progress(trace["status"])
    return trace


def main():
    parser = argparse.ArgumentParser(
        description="Manual real-snapshot automatic versus existing LLM-hypothesis comparison; makes no LLM requests"
    )
    parser.add_argument(
        "--root", type=Path, default=Path(__file__).resolve().parents[2]
    )
    parser.add_argument(
        "--snapshot",
        type=Path,
        default=Path("data/traffic/traffic-8979fdc163fe491a95ca610ed2229033"),
    )
    parser.add_argument("--geography", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument(
        "--arms",
        nargs="+",
        choices=["automatic", "automatic_plus_llm"],
        default=["automatic", "automatic_plus_llm"],
    )
    arguments = parser.parse_args()
    if len(set(arguments.arms)) != len(arguments.arms):
        parser.error("Each arm may be selected only once")
    root, output = arguments.root.resolve(), arguments.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    if (output / "protocol.json").exists():
        raise FileExistsError(
            "Use a new output directory to preserve the frozen protocol"
        )
    snapshot = (
        arguments.snapshot
        if arguments.snapshot.is_absolute()
        else root / arguments.snapshot
    )
    llm_path, input_path = (
        root / "work/network-development/llm-hypotheses.json",
        root / "work/network-development/llm-input.json",
    )
    llm = json.loads(llm_path.read_text())
    if fingerprint(input_path) != llm["input_sha256"]:
        raise ValueError(
            "Saved LLM input differs from the input recorded for its hypotheses"
        )
    hypotheses = [TrafficHypothesis(**row) for row in llm["hypotheses"]]
    started, last = monotonic(), [0.0]

    def checkpoint():
        if monotonic() - last[0] > 30:
            print(
                json.dumps(
                    {"stage": "shared_preparation", "elapsed": monotonic() - started}
                ),
                flush=True,
            )
            last[0] = monotonic()

    prepared = prepare(root, snapshot, checkpoint)
    network = prepared[0]
    bounds = [
        float(network.lon.min()),
        float(network.lat.min()),
        float(network.lon.max()),
        float(network.lat.max()),
    ]
    frozen = output / "frozen-geography.npz"
    RasterGeography.load(arguments.geography, bounds=bounds).save(frozen)
    load_surrogate(ARTIFACT)
    code = source_hashes(root)
    protocol = {
        "created_at": datetime.now(UTC).isoformat(),
        "arms": arguments.arms,
        "mode": "exploratory_single_arm"
        if len(arguments.arms) == 1
        else "ordered_ab_comparison",
        "snapshot": str(snapshot),
        "snapshot_hashes": {
            path.name: fingerprint(path)
            for path in sorted(snapshot.iterdir())
            if path.is_file()
        },
        "geography_sha256": fingerprint(frozen),
        "geography_bounds": bounds,
        "surrogate_sha256": fingerprint(ARTIFACT),
        "llm_hypotheses_sha256": fingerprint(llm_path),
        "llm_input_sha256": fingerprint(input_path),
        "llm_model": llm["model"],
        "llm_hypotheses": len(hypotheses),
        "llm_preexisting_seconds": llm["llm_seconds"],
        "llm_preexisting_usage": llm.get("usage"),
        "max_home_zones": 128,
        "aggregation_initial_cell_km": 2,
        "index_metric": "population_weighted_selected_region_hansen",
        "national_markets": len(prepared[6].cities),
        "git_sha": subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=root, text=True
        ).strip(),
        "source_hashes": code,
        "zones": len(prepared[1]),
        "trips": len(prepared[2]),
        "baseline_indices": [asdict(value) for value in prepared[6].baseline],
        "graph_revision": prepared[6].data.revision,
        "demand_sha256": json.loads(prepared[4].provenance)["demand_sha256"],
        "generation_limit_seconds": development.GENERATION_SECONDS,
        "verification_limit_seconds": development.VERIFICATION_SECONDS,
        "workers": 32,
        "assignment_iterations": 300,
        "assignment_tolerance": 0.001,
        "index_candidate_limit_seconds": development.INDEX_CANDIDATE_SECONDS,
        "mandatory_catboost": True,
        "preparation_seconds": monotonic() - started,
        "comparison_limits": [
            "Single-arm exploration, no A/B comparison"
            if len(arguments.arms) == 1
            else "One ordered A/B run, not a statistical superiority claim",
            "Shared cached baseline and frozen geography",
            "Background machine activity may affect time-bounded coverage",
            "Synthetic demand, no measured traffic",
            "Only solver-converged and index-verified gains count",
            "Existing LLM output reused, no new paid calls",
        ],
    }
    write(output / "protocol.json", protocol)
    results = [
        run_arm(
            name,
            hypotheses if name == "automatic_plus_llm" else [],
            prepared,
            snapshot,
            frozen,
            output,
        )
        for name in protocol["arms"]
    ]
    stable = (
        code == source_hashes(root)
        and protocol["geography_sha256"] == fingerprint(frozen)
        and protocol["surrogate_sha256"] == fingerprint(ARTIFACT)
        and protocol["llm_hypotheses_sha256"] == fingerprint(llm_path)
        and protocol["llm_input_sha256"] == fingerprint(input_path)
        and protocol["snapshot_hashes"]
        == {
            path.name: fingerprint(path)
            for path in sorted(snapshot.iterdir())
            if path.is_file()
        }
    )
    valid_run = stable and all(row["status"] == "completed" for row in results)
    summary = {
        "protocol": str(output / "protocol.json"),
        "source_and_geography_stable": stable,
        "valid_run": valid_run,
        "valid_comparison": valid_run
        and len(results) == 2
        and set(arguments.arms) == {"automatic", "automatic_plus_llm"},
        "arms": results,
    }
    write(output / "result.json", summary)
    print(
        json.dumps(
            {
                "output": str(output / "result.json"),
                "valid_run": summary["valid_run"],
                "valid_comparison": summary["valid_comparison"],
            }
        ),
        flush=True,
    )


if __name__ == "__main__":
    main()
