import json
import os
import shutil
from dataclasses import asdict
from hashlib import file_digest, sha256
from pathlib import Path
from uuid import uuid4
from zipfile import ZIP_DEFLATED, ZipFile

import numpy as np
from synthetic_traffic.assignment import Assignment
from synthetic_traffic.edge_index import EdgeIndex
from synthetic_traffic.incremental import IncrementalBaseline
from synthetic_traffic.incremental_paths import PathCache
from synthetic_traffic.model import Network, Trip
from synthetic_traffic.origin_snapshot import publish_origins, read_origins
from synthetic_traffic.origin_store import OriginStore
from synthetic_traffic.tree_store import ArchiveTrees


def save_baseline(baseline: IncrementalBaseline, destination: Path, metadata: dict | None = None) -> None:
    if not baseline.assignment.converged:
        raise ValueError("Only converged baselines can be published")
    if destination.exists():
        raise FileExistsError(destination)
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = destination.with_name(destination.name + "." + uuid4().hex)
    staging.mkdir()
    try:
        arrays = {}
        network = {}
        for key, value in vars(baseline.network).items():
            if isinstance(value, np.ndarray):
                arrays["network_" + key] = value
            else:
                network[key] = value
        assignment = {}
        for key, value in vars(baseline.assignment).items():
            if isinstance(value, np.ndarray):
                arrays["assignment_" + key] = value
            else:
                assignment[key] = value
        disk_origins = isinstance(baseline.paths.loads, OriginStore)
        if disk_origins:
            arrays.update(trip_origin=np.fromiter((t.origin for t in baseline.trips), dtype=np.int64),
                          trip_destination=np.fromiter((t.destination for t in baseline.trips), dtype=np.int64),
                          trip_vehicles=np.fromiter((t.vehicles_per_hour for t in baseline.trips), dtype=float))
            arrays['od_hours'] = np.asarray([np.nan if value is None else value for value in assignment.pop('od_hours')])
        compact_edges = isinstance(baseline.paths.edges, EdgeIndex)
        if compact_edges:
            arrays.update(edge_keys=baseline.paths.edges.keys_array,
                          edge_weights=baseline.paths.edges.weights,
                          edge_indices=baseline.paths.edges.indices)
        with ZipFile(staging / "arrays.npz", "w", compression=ZIP_DEFLATED) as archive:
            for key, value in arrays.items():
                with archive.open(key + ".npy", "w", force_zip64=True) as stream:
                    np.lib.format.write_array(stream, value, allow_pickle=False)
            for origin, tree in baseline.paths.trees.items():
                for key, value in (("distance", tree.distance), ("parent", tree.parent), ("limit", np.asarray(tree.limit))):
                    with archive.open(f"{key}_{origin}.npy", "w", force_zip64=True) as stream:
                        np.lib.format.write_array(stream, value, allow_pickle=False)
        origin_snapshot = publish_origins(staging / "origins", baseline.paths.loads, baseline.origin_flows) if disk_origins else None
        record = {
            "schema": 5 if disk_origins else (3 if compact_edges else 2),
            "origin_snapshot": origin_snapshot,
            "method": "fixed_od_bpr_msa_origin_flows_v2",
            "metadata": metadata or {},
            "origin_flows": None if disk_origins else {str(origin): list(values.items()) for origin, values in baseline.origin_flows.items()},
            "network": network,
            "assignment": assignment,
            "trips": None if disk_origins else [asdict(trip) for trip in baseline.trips],
            "origins": list(baseline.paths.trees),
            "edges": None if compact_edges else [[u, v, weight, index] for (u, v), (weight, index) in baseline.paths.edges.items()],
            "loads": None if disk_origins else {
                str(origin): {
                    "amounts": [[u, v, amount] for (u, v), amount in amounts.items()],
                    "missing": missing,
                    "times": list(times.items()),
                }
                for origin, (amounts, missing, times) in baseline.paths.loads.items()
            },
            "arrays_sha256": array_digest(staging / "arrays.npz"),
        }
        payload = json.dumps(record, allow_nan=False, separators=(",", ":"))
        (staging / "state.json").write_text(payload)
        (staging / "sha256").write_text(sha256(payload.encode()).hexdigest())
        os.rename(staging, destination)
    finally:
        if staging.exists():
            shutil.rmtree(staging)


def load_baseline(source: Path) -> IncrementalBaseline:
    payload = (source / "state.json").read_bytes()
    if sha256(payload).hexdigest() != (source / "sha256").read_text():
        raise ValueError("Baseline manifest checksum mismatch")
    record = json.loads(payload)
    if record["schema"] not in (2, 3, 4, 5):
        raise ValueError("Unsupported baseline schema")
    if array_digest(source / "arrays.npz") != record["arrays_sha256"]:
        raise ValueError("Baseline arrays checksum mismatch")
    with np.load(source / "arrays.npz", allow_pickle=False) as arrays:
        network = dict(record["network"])
        assignment = dict(record["assignment"])
        for key in arrays.files:
            if key.startswith("network_"):
                network[key.removeprefix("network_")] = arrays[key]
            elif key.startswith("assignment_"):
                assignment[key.removeprefix("assignment_")] = arrays[key]
        if network.get("geometries") is not None:
            network["geometries"] = {int(k): v for k, v in network["geometries"].items()}
        if record['schema'] >= 5:
            trips = [Trip(int(a), int(b), float(c)) for a, b, c in zip(
                arrays['trip_origin'], arrays['trip_destination'], arrays['trip_vehicles'], strict=True)]
            assignment['od_hours'] = [None if np.isnan(value) else float(value) for value in arrays['od_hours']]
        else:
            trips = [Trip(**trip) for trip in record["trips"]]
        paths = object.__new__(PathCache)
        paths.trips = trips
        paths.entries = {}
        for index, trip in enumerate(trips):
            paths.entries.setdefault(trip.origin, []).append((index, trip))
        paths.edges = (EdgeIndex(arrays["edge_keys"], arrays["edge_weights"], arrays["edge_indices"],
                                len(network["raw_nodes"])) if record["schema"] >= 3 else
                       {(int(u), int(v)): (float(w), int(i)) for u, v, w, i in record["edges"]})
        paths.trees = ArchiveTrees(source / "arrays.npz", record["origins"])
        paths.loads = {
            int(origin): (
                {(int(u), int(v)): float(amount) for u, v, amount in row["amounts"]},
                float(row["missing"]),
                {int(i): float(t) for i, t in row["times"]},
            )
            for origin, row in (record["loads"] or {}).items()
        }
        paths.repaired_origins = paths.changed_nodes = 0
        paths._shared_trees = set()
    result = Assignment(**assignment)
    if not result.converged:
        raise ValueError("Stored baseline has not converged")
    if record["schema"] >= 4:
        paths.loads, flows = read_origins(source / "origins", record["origin_snapshot"])
    else:
        flows = {int(origin): {int(edge): float(amount) for edge, amount in values} for origin, values in record["origin_flows"].items()}
    return IncrementalBaseline(Network(**network), trips, result, paths, flows, record.get("metadata", {}))


def array_digest(path: Path) -> str:
    with path.open("rb") as stream:
        return file_digest(stream, "sha256").hexdigest()
