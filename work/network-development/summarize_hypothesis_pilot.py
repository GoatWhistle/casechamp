import argparse
import json
from collections import Counter
from hashlib import sha256
from pathlib import Path

import pyarrow.parquet as pq

LLM_ORIGINS = {"llm", "hypothesis", "agent_hypothesis"}


def pair(left, right):
    return (
        tuple(sorted((int(left), int(right)))) if left is not None and right is not None else None
    )


def parts(project):
    if project.get("kind") == "package":
        return [child for item in project.get("projects", []) for child in parts(item)]
    return [project]


def saved_pairs(protocol, hypotheses):
    rows = pq.read_table(
        Path(protocol["snapshot"]) / "places.parquet",
        columns=["point_id", "settlement", "node"],
    ).to_pylist()
    result = set()
    for hypothesis in hypotheses:
        nodes = []
        for place in (hypothesis["source_place"], hypothesis["target_place"]):
            exact = [row for row in rows if str(row["point_id"]).casefold() == place.casefold()]
            matched = exact or [
                row for row in rows if str(row["settlement"]).casefold() == place.casefold()
            ]
            if len(matched) != 1 or matched[0]["node"] is None:
                raise ValueError("Saved LLM endpoint cannot be resolved unambiguously")
            nodes.append(matched[0]["node"])
        result.add(pair(*nodes))
    return result


def attribution(project, llm_pairs):
    labels, original, exposed, shared, snapped = set(), set(), False, False, False
    final_overlap, llm_sources = False, set()
    for part in parts(project):
        final = pair(part.get("source_node"), part.get("target_node"))
        final_overlap |= final in llm_pairs
        sources = part.get("source_provenance") or [part]
        part_labels = set()
        for source in sources:
            fallback = (
                "automatic_connection" if part.get("kind") == "connection" else "existing_corridor"
            )
            label = source.get(
                "target_origin",
                source.get("origin", source.get("target_reason", fallback)),
            )
            part_labels.add(label)
            previous = pair(
                source.get(
                    "original_source_node",
                    part.get(
                        "original_source_node",
                        source.get("source_node", part.get("source_node")),
                    ),
                ),
                source.get(
                    "original_target_node",
                    part.get(
                        "original_target_node",
                        source.get("target_node", part.get("target_node")),
                    ),
                ),
            )
            if previous in llm_pairs:
                original.add(previous)
                if label in LLM_ORIGINS:
                    exposed = True
                    llm_sources.add(previous)
                    snapped |= previous != final
        labels.update(part_labels)
        shared |= bool(part_labels & LLM_ORIGINS) and bool(part_labels - LLM_ORIGINS)
    return {
        "origins": sorted(labels),
        "llm_exposed": exposed,
        "merged_sources": shared,
        "snapped_llm": snapped,
        "llm_original_pairs": sorted(original),
        "llm_provenance_pairs": sorted(llm_sources),
        "final_pair_overlap": final_overlap,
        "llm_exclusive": exposed and not bool(labels - LLM_ORIGINS),
    }


def origin_counts(projects, llm_pairs):
    return dict(
        Counter(
            label for project in projects for label in attribution(project, llm_pairs)["origins"]
        )
    )


def summarize_arm(name, candidates, trace, llm_pairs, baseline_score):
    targets = candidates.get("target_proposals", [])
    corridors = candidates.get("connections_for_review", [])
    target_info = [attribution(row, llm_pairs) for row in targets]
    corridor_info = [attribution(row, llm_pairs) for row in corridors]
    attempts = []
    represented = set()
    for row in trace.get("index_attempts", []):
        info = attribution(row.get("project", {}), llm_pairs)
        verified = row.get("status") == "index_verified"
        gain = row["weighted_regional_index"] - baseline_score if verified else None
        if verified and info["llm_exposed"]:
            represented.update(tuple(value) for value in info["llm_provenance_pairs"])
        attempts.append(
            {
                "status": row.get("status"),
                "kind": row.get("project", {}).get("kind"),
                "index_gain": gain,
                "index_seconds": row.get("index_seconds"),
                **info,
            }
        )
    verified = [row for row in attempts if row["status"] == "index_verified"]
    exposed = [row for row in verified if row["llm_exposed"]]
    return {
        "arm": name,
        "status": trace.get("status", "missing"),
        "llm_forwarded": trace.get("llm_forwarded_count", 0),
        "published_target_count": len(targets),
        "corridor_variants": len(corridors),
        "llm_exposed_published_targets": sum(row["llm_exposed"] for row in target_info),
        "llm_exposed_corridor_variants": sum(row["llm_exposed"] for row in corridor_info),
        "merged_llm_automatic_corridor_variants": sum(
            row["merged_sources"] for row in corridor_info
        ),
        "snapped_llm_corridor_variants": sum(row["snapped_llm"] for row in corridor_info),
        "original_pair_overlap_corridors": sum(
            bool(row["llm_original_pairs"]) for row in corridor_info
        ),
        "final_pair_overlap_corridors": sum(row["final_pair_overlap"] for row in corridor_info),
        "corrected_candidate_origin_counts": origin_counts(corridors, llm_pairs),
        "index_verified_projects": len(verified),
        "index_timeout_projects": len(attempts) - len(verified),
        "llm_exposed_index_verified_projects": len(exposed),
        "llm_exclusive_index_verified_projects": sum(row["llm_exclusive"] for row in verified),
        "llm_original_pairs_index_verified": len(represented),
        "best_index_gain": max((row["index_gain"] for row in verified), default=None),
        "best_llm_exposed_index_gain": max((row["index_gain"] for row in exposed), default=None),
        "target_diagnostics": candidates.get("target_diagnostics", {}),
        "index_attempts": attempts,
        "benefits": trace.get("benefits", []),
        "timings": {
            key: trace.get("evidence", {}).get(key)
            for key in (
                "generation_seconds",
                "verification_seconds",
                "total_development_seconds",
            )
        },
    }


def summarize(run, hypotheses_path):
    protocol = json.loads((run / "protocol.json").read_text())
    raw = hypotheses_path.read_bytes()
    if sha256(raw).hexdigest() != protocol["llm_hypotheses_sha256"]:
        raise ValueError("LLM hypotheses differ from the frozen protocol")
    hypotheses = json.loads(raw)["hypotheses"]
    llm_pairs = saved_pairs(protocol, hypotheses)
    population = sum(row["population"] for row in protocol["baseline_indices"])
    baseline_score = (
        sum(row["value"] * row["population"] for row in protocol["baseline_indices"]) / population
    )
    arms = []
    for name in protocol["arms"]:
        candidate_path, trace_path = (
            run / f"{name}-candidates.json",
            run / f"{name}-result.json",
        )
        candidates = json.loads(candidate_path.read_text()) if candidate_path.exists() else {}
        trace = json.loads(trace_path.read_text()) if trace_path.exists() else {}
        arms.append(summarize_arm(name, candidates, trace, llm_pairs, baseline_score))
    final_path = run / "result.json"
    frozen_result = json.loads(final_path.read_text()) if final_path.exists() else {}
    return {
        "protocol": str(run / "protocol.json"),
        "paid_llm_requests": 0,
        "saved_llm_hypotheses": len(hypotheses),
        "unique_original_pairs": len(llm_pairs),
        "baseline_weighted_regional_index": baseline_score,
        "frozen_runner_valid_comparison": frozen_result.get("valid_comparison"),
        "frozen_runner_valid_run": frozen_result.get("valid_run"),
        "has_index_verification_in_both_arms": len(arms) == 2
        and all(row["index_verified_projects"] > 0 for row in arms),
        "complete_arms": all(row["status"] == "completed" for row in arms),
        "interpretation": [
            "Merged provenance records exposure, not a unique causal LLM contribution",
            "Original endpoint matching survives road-access snapping; final-pair overlap is separately reported",
        ],
        "arms": arms,
    }


def main():
    parser = argparse.ArgumentParser(
        description="Recalculate provenance attribution from a frozen hypothesis pilot"
    )
    parser.add_argument("--run", type=Path, required=True)
    parser.add_argument(
        "--hypotheses",
        type=Path,
        default=Path(__file__).resolve().parent / "llm-hypotheses.json",
    )
    parser.add_argument("--output", type=Path)
    arguments = parser.parse_args()
    output = arguments.output or arguments.run / "attribution-summary.json"
    protected = {
        "protocol.json",
        "result.json",
        "automatic-result.json",
        "automatic_plus_llm-result.json",
        "automatic-candidates.json",
        "automatic_plus_llm-candidates.json",
    }
    if output.name in protected:
        raise ValueError("Postprocessing cannot overwrite frozen pilot inputs or results")
    result = summarize(arguments.run, arguments.hypotheses)
    output.parent.mkdir(parents=True, exist_ok=True)
    temporary = output.with_suffix(output.suffix + ".tmp")
    temporary.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    temporary.replace(output)
    print(
        json.dumps(
            {
                "output": str(output),
                "verified_both": result["has_index_verification_in_both_arms"],
            }
        )
    )


if __name__ == "__main__":
    main()
