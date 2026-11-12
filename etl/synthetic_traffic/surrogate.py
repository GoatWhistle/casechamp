import json
from hashlib import sha256
from pathlib import Path

import numpy as np
from catboost import CatBoostRegressor
from synthetic_traffic.assignment import Assignment
from synthetic_traffic.model import Network, Trip, Zone
from synthetic_traffic.surrogate_features import (
    CONNECTION_FEATURES,
    build_feature_context,
    connection_features,
)

SCHEMA_VERSION = 2

ARTIFACT = Path(__file__).with_name("surrogate.cbm")
FEATURES = [
    "kind",
    "edges",
    "length",
    "flow",
    "delay",
    "ratio",
    "free",
    "capacity",
    "extra_lanes",
    "parts",
] + CONNECTION_FEATURES


def accessibility(
    assignment: Assignment, trips: list[Trip], zones: list[Zone] | None = None
) -> float:
    populations = {zone.node: zone.population for zone in zones or []}
    weights = np.asarray(
        [
            populations.get(trip.origin, trip.vehicles_per_hour)
            * populations.get(trip.destination, 1.0)
            for trip in trips
        ]
    )
    values = np.asarray(
        [0.0 if t is None else np.exp(-np.log(2) * t) for t in assignment.od_hours]
    )
    return float(weights @ values / weights.sum()) if weights.sum() else 0.0


def features(
    network: Network, baseline: Assignment, project: dict, context=None
) -> list[float]:
    parts = []
    pending = [project]
    while pending:
        part = pending.pop()
        if part.get("kind") == "package":
            pending.extend(part.get("projects", []))
        elif part.get("kind") in {"capacity", "connection", "closure", "opening"}:
            parts.append(part)
        else:
            raise ValueError(
                "Unsupported project kind for the road development surrogate"
            )
    selected = np.isin(
        network.way_id, [way for part in parts for way in part.get("way_ids", [])]
    )
    kinds = {
        "capacity": 2,
        "connection": 3,
        "package": 4,
        "closure": 5,
        "opening": 6,
    }
    context = context or build_feature_context(network, baseline)
    if context.network is not network or context.baseline is not baseline:
        raise ValueError("Feature context belongs to another assignment")
    return [
        float(kinds.get(project["kind"], 0)),
        float(selected.sum()),
        float(network.length_km[selected].sum())
        + sum(float(p.get("length_km", 0)) for p in parts),
        float(baseline.flow[selected].sum()),
        float(
            (
                baseline.flow[selected]
                * np.maximum(baseline.hours[selected] - network.free_hours[selected], 0)
            ).sum()
        ),
        float(baseline.ratio[selected].max(initial=0)),
        float(network.free_hours[selected].sum()),
        float(network.capacity[selected].sum()),
        float(
            sum(
                int(p.get("extra_lanes", 1))
                for p in parts
                if p.get("kind") == "capacity"
            )
        ),
        float(len(parts)),
    ] + connection_features(context, parts)


def load_surrogate(path: Path = ARTIFACT) -> CatBoostRegressor:
    if not path.is_file():
        raise RuntimeError(
            f"Required CatBoost surrogate artifact is missing: {path}; run python -m synthetic_traffic.training"
        )
    manifest = path.with_suffix(".json")
    if not manifest.is_file():
        raise RuntimeError("Required CatBoost training manifest is missing")
    metadata = json.loads(manifest.read_text())
    if metadata.get("artifact_sha256") != sha256(path.read_bytes()).hexdigest():
        raise RuntimeError(
            "CatBoost artifact checksum does not match its training manifest"
        )
    if (
        metadata.get("schema_version") != SCHEMA_VERSION
        or metadata.get("feature_schema") != FEATURES
    ):
        raise RuntimeError(
            "CatBoost surrogate feature schema is incompatible; retrain required"
        )
    model = CatBoostRegressor(thread_count=1)
    try:
        model.load_model(str(path))
    except Exception as error:
        raise RuntimeError(f"Cannot load required CatBoost artifact: {path}") from error
    if model.feature_names_ != FEATURES:
        raise RuntimeError("CatBoost surrogate feature schema is incompatible")
    return model
