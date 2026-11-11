import hashlib
import json
from pathlib import Path

from road_traffic.candidates import candidate_roads
from road_traffic.inputs import refresh_inputs
from road_traffic.inventory import attributes, coverage
from road_traffic.matching import match_observations
from road_traffic.observations import collect_observations
from road_traffic.reports import report
from road_traffic.snapshot import checkpoint, json_text, snapshot, validate_snapshot
from road_traffic.storage import Storage


def observations(store, run_id, root, output, graph_revision):
    for table in ["sources", "traffic_observations", "graph_matches"]:
        store.clear(table, run_id)
    obs, sources = collect_observations(root, root / "data/additional/road-traffic")
    store.insert(
        "sources",
        [
            {"run_id": run_id, "source_id": row["source_id"], "record": json_text(row)}
            for row in sources
        ],
    )
    store.insert(
        "traffic_observations",
        [
            {
                "run_id": run_id,
                **{
                    k: row.get(k)
                    for k in [
                        "observation_id",
                        "source_id",
                        "region_id",
                        "value",
                        "unit",
                        "period",
                    ]
                },
                "record": json_text(row),
            }
            for row in obs
        ],
    )
    confirmations_path = root / "datasets/additional/road-traffic/confirmations.json"
    confirmations = (
        json.loads(confirmations_path.read_text())
        if confirmations_path.exists()
        else []
    )
    roads = candidate_roads(
        store,
        obs,
        ("plexus_traffic_snapshot_" + run_id),
        root / "data/additional/road-traffic/candidate-cache" / run_id,
    )
    if confirmations:
        if any(
            c.get("graph_revision") != graph_revision or not c.get("evidence")
            for c in confirmations
        ):
            raise ValueError(
                "Confirmation requires matching graph revision and evidence"
            )
        ids = sorted({int(c["way_id"]) for c in confirmations})
        selected = ",".join(map(str, ids))
        roads.extend(
            store.rows(
                f"SELECT way_id,name,highway,coordinates FROM {('plexus_traffic_snapshot_' + run_id)}.road_lines WHERE way_id IN ({selected})"
            )
        )
    matches = match_observations(obs, roads, graph_revision, confirmations)
    store.insert(
        "graph_matches",
        [
            {
                "run_id": run_id,
                "observation_id": row["observation_id"],
                "status": row["status"],
                "record": json_text(row),
            }
            for row in matches
        ],
    )
    return {"observations": len(obs), "sources": len(sources)}


def run(root, output, run_id=None, database="plexus_traffic", only=None):
    collect_observations(root, root / "data/additional/road-traffic")
    store = Storage(database)
    store.initialize()
    manifest = root / "data/road-refresh/graph/manifest.json"
    code = b"".join(p.read_bytes() for p in sorted(Path(__file__).parent.glob("*.py")))
    revision = hashlib.sha256(manifest.read_bytes()).hexdigest()
    run_id = run_id or hashlib.sha256(revision.encode() + code).hexdigest()[:24]
    if not run_id.isalnum() or len(run_id) > 40:
        raise ValueError("Invalid run ID")
    previous = store.rows(
        f"SELECT record FROM {database}.runs FINAL WHERE run_id='{run_id}'"
    )
    state = (
        json.loads(previous[0]["record"])
        if previous
        else {"graph_revision": revision, "stages": {}}
    )
    if state["graph_revision"] != revision:
        raise ValueError("Source revision changed")
    if only == "coverage" and "attributes" not in state["stages"]:
        raise ValueError("Coverage requires completed attributes stage")
    if only == "observations" and "coverage" not in state["stages"]:
        raise ValueError("Observation matching requires completed coverage stage")
    refresh_inputs(root, state)
    source = snapshot(store, run_id)
    validate_snapshot(store, source, state)
    state["snapshot"] = source
    output.mkdir(parents=True, exist_ok=True)
    checkpoint(store, run_id, state)
    try:
        for stage, action in [
            ("attributes", lambda: attributes(store, run_id, source)),
            ("coverage", lambda: coverage(store, run_id, source)),
            (
                "observations",
                lambda: observations(store, run_id, root, output, revision),
            ),
        ]:
            if only and stage != only:
                continue
            if only == stage:
                state["stages"].pop(stage, None)
                if stage == "attributes":
                    state["stages"].pop("coverage", None)
                if stage in {"attributes", "coverage"}:
                    state["stages"].pop("observations", None)
                state.pop("report", None)
                store.clear("regional_coverage", run_id)
            if stage not in state["stages"]:
                state["stages"][stage] = action()
                checkpoint(store, run_id, state)
        if not only:
            state["report"] = report(store, run_id, source, output, root)
        completed = not only and all(
            k in state["stages"] for k in ["attributes", "coverage", "observations"]
        )
        checkpoint(store, run_id, state, "completed" if completed else "partial")
    except Exception as error:
        state["error"] = str(error)
        checkpoint(store, run_id, state, "failed")
        raise
    print(json_text({"run_id": run_id, **state}), flush=True)
