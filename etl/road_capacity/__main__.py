import argparse
import hashlib
import json
import os
from pathlib import Path

from .aggregate import rebuild_indices
from .atlas import rebuild_atlas
from .checkpoints import fingerprint, verify_checkpoints, write_state
from .matrices import rebuild_matrices
from .reference import references
from .storage import CapacityStore, freeze
from .weights import replace_weights


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "stage", choices=["prepare", "weights", "matrices", "indices", "atlas", "all"]
    )
    parser.add_argument("--root", type=Path, default=Path.cwd())
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--workers",
        type=int,
        choices=range(1, 49),
        default=min(8, os.cpu_count() or 1),
        metavar="1..48",
    )
    parser.add_argument(
        "--restart-from", choices=["weights", "matrices", "indices", "atlas"]
    )
    args = parser.parse_args()
    output = args.output or args.root / "data/road-capacity"
    output.mkdir(parents=True, exist_ok=True)
    store = CapacityStore()
    source = freeze(store, output)
    reference = references(store, output)
    state_path = output / "state.json"
    state = (
        json.loads(state_path.read_text())
        if state_path.exists()
        else {"source": source, "reference": reference, "stages": {}}
    )
    if state["source"] != source or state["reference"] != reference:
        raise ValueError("Frozen source identity changed")
    verify_checkpoints(state, reference, source, args.restart_from)
    revision = hashlib.sha256(
        json.dumps(source, sort_keys=True).encode() + b"road-capacity-v1"
    ).hexdigest()
    actions = {
        "weights": lambda: replace_weights(store),
        "matrices": lambda: rebuild_matrices(
            store, args.root, output, reference, revision, args.workers
        ),
        "indices": lambda: rebuild_indices(store, reference),
        "atlas": lambda: rebuild_atlas(store, source, reference),
    }
    dependencies = {
        "weights": [],
        "matrices": ["weights"],
        "indices": ["matrices"],
        "atlas": ["indices"],
    }
    for stage, action in actions.items():
        if args.stage not in {stage, "all"} or stage in state["stages"]:
            continue
        if any(required not in state["stages"] for required in dependencies[stage]):
            raise ValueError(f"Missing prerequisite stage for {stage}")
        state["stages"][stage] = action()
        state["stage_fingerprints"][stage] = fingerprint(stage, reference, source)
        write_state(state_path, state)
    write_state(state_path, state)
    print(json.dumps(state, ensure_ascii=False, allow_nan=False), flush=True)


if __name__ == "__main__":
    main()
