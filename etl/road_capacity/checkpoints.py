import hashlib
import json
from pathlib import Path

import inequality
from app.adapter.road_graph import data, routing, shortest_paths
from app.domain import road_cost, road_profiles

STAGES = ["weights", "matrices", "indices", "atlas"]


def fingerprint(stage, reference, source):
    folder = Path(__file__).parent
    files = {
        "weights": [
            folder / "weights.py",
            Path(road_cost.__file__),
            Path(road_profiles.__file__),
        ],
        "matrices": [
            folder / name for name in ["matrices.py", "metrics.py", "network.py"]
        ]
        + [Path(module.__file__) for module in [data, routing, shortest_paths]],
        "indices": [folder / "aggregate.py", Path(inequality.__file__)],
        "atlas": [folder / "atlas.py"],
    }[stage]
    digest = hashlib.sha256(
        json.dumps({"reference": reference, "source": source}, sort_keys=True).encode()
    )
    for path in sorted(files):
        contents = path.read_bytes()
        digest.update(
            path.name.encode() + b"\0" + str(len(contents)).encode() + b"\0" + contents
        )
    return digest.hexdigest()


def verify_checkpoints(state, reference, source, restart=None):
    if restart:
        for stage in STAGES[STAGES.index(restart) :]:
            state["stages"].pop(stage, None)
            state.setdefault("stage_fingerprints", {}).pop(stage, None)
    recorded = state.setdefault("stage_fingerprints", {})
    for stage in state["stages"]:
        current = fingerprint(stage, reference, source)
        if stage not in recorded:
            state.setdefault("adopted_unversioned_checkpoints", []).append(stage)
            recorded[stage] = current
        elif recorded[stage] != current:
            raise ValueError(
                f"Implementation changed for {stage}; use --restart-from {stage}"
            )


def write_state(path, state):
    temporary = path.with_suffix(".tmp")
    temporary.write_text(
        json.dumps(state, ensure_ascii=False, indent=2, allow_nan=False)
    )
    temporary.replace(path)
