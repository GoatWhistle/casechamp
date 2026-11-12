import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
from catboost import CatBoostRegressor, Pool
from synthetic_traffic.assignment import assign
from synthetic_traffic.projects import apply_project
from synthetic_traffic.surrogate import (
    ARTIFACT,
    FEATURES,
    SCHEMA_VERSION,
    accessibility,
    build_feature_context,
    features,
)
from synthetic_traffic.training_metrics import ranking_metrics
from synthetic_traffic.training_scenarios import scenario
from synthetic_traffic.training_snapshots import snapshot_rows


def train(
    path: Path = ARTIFACT,
    scenarios: int = 24,
    seed: int = 20261112,
    snapshots: list[Path] | None = None,
    candidate_file: Path | None = None,
) -> dict:
    if scenarios < 8:
        raise ValueError("At least eight independent network scenarios are required")
    rows, labels, groups = [], [], []
    unconverged = 0
    for group in range(scenarios):
        network, trips, projects = scenario(seed + group)
        baseline = assign(network, trips, iterations=150, tolerance=1e-3)
        unconverged += int(not baseline.converged)
        if not baseline.converged:
            continue
        base = accessibility(baseline, trips)
        context = build_feature_context(network, baseline)
        for project in projects:
            try:
                changed = apply_project(network, project)
            except ValueError:
                continue
            after = assign(changed, trips, iterations=150, tolerance=1e-3)
            unconverged += int(not after.converged)
            if not after.converged:
                continue
            rows.append(features(network, baseline, project, context=context))
            labels.append(accessibility(after, trips) - base)
            groups.append(group)
    snapshot_reports = []
    for index, snapshot in enumerate(snapshots or []):
        real_rows, real_labels, report = snapshot_rows(
            snapshot, candidate_file=candidate_file
        )
        rows.extend(real_rows)
        labels.extend(real_labels)
        groups.extend([scenarios + index] * len(real_rows))
        snapshot_reports.append(report)
    x, y, groups = np.asarray(rows), np.asarray(labels), np.asarray(groups)
    split = int(scenarios * 0.75)
    heldout = (groups >= split) & (groups < scenarios)
    if snapshots:
        heldout |= groups == scenarios + len(snapshots) - 1
    model = CatBoostRegressor(
        iterations=160,
        depth=5,
        learning_rate=0.06,
        random_seed=seed,
        thread_count=1,
        verbose=False,
        allow_writing_files=False,
    )
    model.fit(Pool(x[~heldout], y[~heldout], feature_names=FEATURES))
    all_predictions = np.asarray(model.predict(x, thread_count=1))
    predictions = all_predictions[heldout]
    selected_gains, best_gains, deterministic_gains, rankings = [], [], [], []
    for group in np.unique(groups[heldout]):
        mask = groups[heldout] == group
        selected_gains.append(float(y[heldout][mask][np.argmax(predictions[mask])]))
        best_gains.append(float(y[heldout][mask].max()))
        deterministic_gains.append(
            float(y[heldout][mask][np.argmax(x[heldout][mask, 4])])
        )
        rankings.append(
            {
                "group": int(group),
                "samples": int(mask.sum()),
                "selected_gain": selected_gains[-1],
                "deterministic_gain": deterministic_gains[-1],
                "oracle_gain": best_gains[-1],
            }
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    model.save_model(str(path))
    report = {
        "schema_version": SCHEMA_VERSION,
        "new_road_heldout": ranking_metrics(
            x, y, all_predictions, groups, heldout & (x[:, 10] > 0)
        ),
        "positive_labels": int((y > 0).sum()),
        "negative_labels": int((y < 0).sum()),
        "created_at": datetime.now(UTC).isoformat(),
        "seed": seed,
        "synthetic_scenarios_requested": scenarios,
        "candidate_file": str(candidate_file) if candidate_file else None,
        "feature_basis": "Simulated incident edge flow and delay; exact current endpoint shortest travel; proposed equivalent travel time. No observed demand or LLM priority features.",
        "feature_schema": FEATURES,
        "project_kinds": ["capacity", "closure", "connection", "package"],
        "excluded_interventions": ["standalone_speed"],
        "training_scenarios": len(np.unique(groups[~heldout])),
        "heldout_scenarios": len(np.unique(groups[heldout])),
        "training_samples": int((~heldout).sum()),
        "heldout_samples": int(heldout.sum()),
        "split": "final quarter of synthetic seeds and last real snapshot held out",
        "label": "fixed OD flow-weighted exponential accessibility delta, half-life 1 hour",
        "solver": {
            "algorithm": "full MSA assignment",
            "iterations": 150,
            "tolerance": 1e-3,
        },
        "unconverged_label_solves": unconverged,
        "heldout_mae": float(np.abs(predictions - y[heldout]).mean()),
        "heldout_zero_predictor_mae": float(np.abs(y[heldout]).mean()),
        "snapshot_corpus": snapshot_reports,
        "heldout_rankings": rankings,
        "heldout_deterministic_delay_priority_mean_gain": float(
            np.mean(deterministic_gains)
        ),
        "heldout_selected_mean_gain": float(np.mean(selected_gains)),
        "heldout_oracle_mean_gain": float(np.mean(best_gains)),
        "artifact_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
        "limitations": [
            "Small synthetic corpus and two clipped road snapshots; no national or observed traffic validation",
            "Road snapshots overlap geographically and share sourced candidate alignments; heldout snapshot is not independent geographic validation",
            "Local accessibility labels do not train national Hansen index, transit or congestion objectives",
            "Unconverged MSA labels excluded; only converged simulated labels used",
            "Connections and mixed packages included; physical construction feasibility is not a training label",
            "Surrogate orders evaluations only; returned effects require solver verification",
            "Numerical training labels do not establish construction clearance; generated capacity projects require sourced raster screening",
        ],
    }
    corpus = path.with_name(path.stem + "-corpus.npz")
    np.savez_compressed(corpus, features=x, labels=y, groups=groups, heldout=heldout)
    report["corpus_sha256"] = hashlib.sha256(corpus.read_bytes()).hexdigest()
    report["corpus_file"] = corpus.name
    path.with_suffix(".json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ARTIFACT)
    parser.add_argument("--scenarios", type=int, default=24)
    parser.add_argument("--snapshot", action="append", type=Path, default=[])
    parser.add_argument("--candidates", type=Path)
    parser.add_argument("--seed", type=int, default=20261112)
    args = parser.parse_args()
    print(
        json.dumps(
            train(
                args.output, args.scenarios, args.seed, args.snapshot, args.candidates
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
