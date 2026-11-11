import hashlib
from pathlib import Path


def refresh_inputs(root, state):
    inputs = [
        Path(__file__).with_name(n)
        for n in [
            "observations.py",
            "sources.py",
            "new_surveys.py",
            "matching.py",
            "candidates.py",
        ]
    ]
    inputs += list((root / "data/additional/traffic-surveys").glob("*.csv"))
    inputs += list((root / "datasets/additional/road-traffic").glob("*.json"))
    digest_builder = hashlib.sha256()
    for path in sorted(inputs):
        if path.exists():
            name = str(path.resolve()).encode()
            payload = path.read_bytes()
            digest_builder.update(len(name).to_bytes(8, "big") + name)
            digest_builder.update(len(payload).to_bytes(8, "big") + payload)
    digest = digest_builder.hexdigest()
    if state.get("observation_input_digest") != digest:
        state["stages"].pop("observations", None)
        state.pop("report", None)
    state["observation_input_digest"] = digest
    state.pop("error", None)
