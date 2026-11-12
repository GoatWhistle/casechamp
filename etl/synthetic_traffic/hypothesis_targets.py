import time

import numpy as np
from scipy.sparse.csgraph import dijkstra
from synthetic_traffic.assignment import route_graph


def prepare_hypotheses(
    network, access, hypotheses, geography_groups=None, deadline=None, check=None
):
    available = np.asarray(access, dtype=int)
    allowed = set(available.tolist())
    raw = {int(value): index for index, value in enumerate(network.raw_nodes)}
    whitelist = (
        set(map(int, network.access_raw_nodes))
        if network.access_raw_nodes is not None
        else set(raw)
    )
    if any(int(network.raw_nodes[node]) not in whitelist for node in available):
        raise ValueError(
            "Eligible snap destinations must belong to the source road-access whitelist"
        )
    cache = {}
    graph = None
    rejected = {}
    details = []
    prepared = []
    snapped = 0
    skipped_index = 0

    def reject(hypothesis, reason):
        nonlocal skipped_index
        rejected[reason] = rejected.get(reason, 0) + 1
        skipped_index += int(hypothesis.get("origin") == "index_route")
        if len(details) < 128:
            details.append(
                {
                    "source_node": hypothesis.get("source_node"),
                    "target_node": hypothesis.get("target_node"),
                    "origin": hypothesis.get("origin", "hypothesis"),
                    "reason": reason,
                }
            )

    def snap(node):
        nonlocal graph
        if node in allowed:
            return node, 0.0
        if node not in cache:
            if check:
                check()
            if deadline is not None and time.monotonic() >= deadline:
                return None
            if not len(available):
                cache[node] = None
            else:
                if graph is None:
                    graph, _ = route_graph(network, network.length_km)
                distances = dijkstra(graph, directed=True, indices=node, limit=2.0)
                options = distances[available]
                best = int(np.argmin(options))
                cache[node] = (
                    (int(available[best]), float(options[best]))
                    if np.isfinite(options[best]) and options[best] <= 2
                    else None
                )
        return cache[node]

    for hypothesis in hypotheses or []:
        if check:
            check()
        if not isinstance(hypothesis, dict):
            raise TypeError("Corridor hypotheses require endpoint objects")
        ids = [hypothesis.get("source_node"), hypothesis.get("target_node")]
        invalid = any(
            isinstance(value, bool) or not isinstance(value, int) or value not in raw
            for value in ids
        )
        if invalid:
            if hypothesis.get("origin") == "index_route":
                reject(hypothesis, "index_endpoint_outside_stored_network")
                continue
            raise ValueError(
                "Hypothesis endpoints must be exact stored road-network node IDs"
            )
        if ids[0] == ids[1]:
            raise ValueError(
                "Hypothesis endpoints must be distinct stored road-network nodes"
            )
        priority = hypothesis.get("priority", 0.0)
        if (
            isinstance(priority, bool)
            or not isinstance(priority, (int, float))
            or not np.isfinite(priority)
        ):
            raise ValueError("Hypothesis priority must be finite")
        if deadline is not None and time.monotonic() >= deadline:
            reject(hypothesis, "generation_deadline")
            continue
        endpoints = [snap(raw[value]) for value in ids]
        if any(value is None for value in endpoints):
            reject(hypothesis, "no_eligible_access_within_2km_existing_road")
            continue
        (a, source_km), (b, target_km) = endpoints
        if a == b:
            reject(hypothesis, "endpoints_snap_to_same_access_node")
            continue
        if geography_groups and geography_groups.get(a) != geography_groups.get(b):
            reject(hypothesis, "snap_endpoints_in_separate_geographic_components")
            continue
        snapped += int(source_km > 0 or target_km > 0)
        metadata = {
            "target_origin": str(hypothesis.get("origin", "hypothesis")),
            "target_rationale": str(hypothesis.get("reason", ""))[:1000],
            "hypothesis_reason": hypothesis.get("reason", ""),
            "target_priority": float(priority),
            "original_source_node": ids[0],
            "original_target_node": ids[1],
            "source_snap_road_km": source_km,
            "target_snap_road_km": target_km,
            "snap_basis": "existing_directed_road_length_within_2km_unverified_project",
        }
        prepared.append((a, b, "validated_hypothesis", 1.0, metadata))
    return prepared, {
        "hypotheses_requested": len(hypotheses or []),
        "hypotheses_accepted_for_screening": len(prepared),
        "hypotheses_snapped_to_road_access": snapped,
        "hypothesis_snap_dijkstra_origins": len(cache),
        "hypothesis_rejection_counts": rejected,
        "hypothesis_rejections": details,
        "index_hints_outside_eligible_geography": skipped_index,
    }


def diversify_targets(rows, limit, diagnostics=None):
    def hypothesis(row):
        sources = row.get("source_provenance", [row])
        return any(
            source.get("target_origin") in {"llm", "hypothesis", "agent_hypothesis"} for source in sources
        )

    hints = [row for row in rows if hypothesis(row)]
    ordinary = [row for row in rows if not hypothesis(row)]
    quota = min(len(hints), max(1, limit // 4)) if hints else 0
    selected = hints[:quota]
    ordinary.extend(hints[quota:])
    result = []
    while len(result) < limit and (ordinary or selected):
        if selected and (len(result) % 4 == 0 or not ordinary):
            result.append(selected.pop(0))
        elif ordinary:
            result.append(ordinary.pop(0))
    if diagnostics is not None:
        diagnostics["hypothesis_diversity_quota"] = quota
        diagnostics["hypothesis_pairs_in_target_pool"] = sum(
            hypothesis(row) for row in result
        )
    return result
