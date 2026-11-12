import hashlib
import json
from pathlib import Path

import numpy as np
from synthetic_traffic.assignment import assign
from synthetic_traffic.demand import aggregate, generate
from synthetic_traffic.model import DemandParameters
from synthetic_traffic.projects import apply_project
from synthetic_traffic.source import load_network, load_places
from synthetic_traffic.surrogate import accessibility, build_feature_context, features


def snapshot_rows(
    path: Path, limit: int = 12, candidate_file: Path | None = None
) -> tuple[list, list, dict]:
    network = load_network(path)
    zones, _ = load_places(path, network)
    zones, _ = aggregate(zones, network, cell_km=2, max_zones=12)
    trips, _ = generate(network, zones, DemandParameters())
    baseline = assign(network, trips, iterations=150, tolerance=1e-3)
    if not baseline.converged:
        return [], [], {"snapshot": path.name, "status": "baseline_not_converged"}
    priorities = baseline.flow * np.maximum(baseline.hours - network.free_hours, 0)
    ways = list(dict.fromkeys(network.way_id[np.argsort(-priorities)].tolist()))[:limit]
    rows, labels, skipped = [], [], 0
    base = accessibility(baseline, trips)
    context = build_feature_context(network, baseline)
    projects = [
        {"kind": kind, "way_ids": [int(way)]}
        for way in ways
        for kind in ("capacity", "closure")
    ]
    if candidate_file is not None:
        connections = json.loads(candidate_file.read_text())["connections_for_review"]
        known = set(network.raw_nodes.tolist())
        connections = [
            p
            for p in connections
            if p["source_node"] in known and p["target_node"] in known
        ]
        projects.extend(connections)
        projects.extend(
            {"kind": "package", "projects": [a, b]}
            for a, b in zip(connections[::2], connections[1::2])
        )
        projects.extend(
            {
                "kind": "package",
                "projects": [
                    p,
                    {"kind": "capacity", "way_ids": [int(ways[i % len(ways)])]},
                ],
            }
            for i, p in enumerate(connections[:8])
        )
    for project in projects:
        try:
            changed = apply_project(network, project)
        except ValueError:
            continue
        after = assign(changed, trips, iterations=150, tolerance=1e-3)
        if not after.converged:
            skipped += 1
            continue
        rows.append(features(network, baseline, project, context=context))
        labels.append(accessibility(after, trips) - base)
    return (
        rows,
        labels,
        {
            "candidate_source_sha256": hashlib.sha256(
                candidate_file.read_bytes()
            ).hexdigest()
            if candidate_file
            else None,
            "connections": sum(row[10] > 0 for row in rows),
            "snapshot": path.name,
            "source_hashes": {
                name: hashlib.sha256((path / name).read_bytes()).hexdigest()
                for name in ["nodes.parquet", "edges.parquet", "places.parquet"]
            },
            "status": "labelled",
            "edges": len(network.source),
            "trips": len(trips),
            "samples": len(rows),
            "unconverged_excluded": skipped,
            "limits": "Real road topology; synthetic gravity demand; no observed traffic validation",
        },
    )
