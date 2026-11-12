import json
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
from synthetic_traffic.candidates import generate_candidates
from synthetic_traffic.source import load_network


def search(
    snapshot: Path, baseline: Path, output: Path, multiplier: float, limit: int
) -> dict:
    if output.exists():
        raise ValueError("Candidate output exists; choose a new file")
    network = load_network(snapshot)
    report = json.loads((baseline / "report.json").read_text())
    source = json.loads((snapshot / "source.json").read_text())
    if report["metadata"]["source"].get("sha256") != source.get("sha256"):
        raise ValueError("Baseline input checksums do not match the network snapshot")
    case = next((c for c in report["cases"] if c["multiplier"] == multiplier), None)
    if case is None or not case["baseline"]["converged"]:
        raise ValueError(
            "Choose a converged baseline at the requested demand multiplier"
        )
    table = pq.read_table(baseline / case["baseline"]["edge_flows"])
    checks = [
        ("way_id", network.way_id),
        ("source_node", network.raw_nodes[network.source]),
        ("target_node", network.raw_nodes[network.target]),
    ]
    if any(
        not np.array_equal(table[name].to_numpy(), values) for name, values in checks
    ):
        raise ValueError("Baseline edge identities/order do not match the snapshot")
    result = generate_candidates(
        network,
        table["flow"].to_numpy(),
        table["hours"].to_numpy(),
        table["demand_capacity_ratio"].to_numpy(),
        limit,
    )
    result.update(
        method="bounded_traffic_candidate_screen_v1",
        demand_sha256=report["demand_sha256"],
        multiplier=multiplier,
        screening_only=True,
        limits=[
            "No engineering feasibility or cost approval",
            "No global optimum claim",
            "Candidates need full same-demand reassignment before comparing benefit",
        ],
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return result
