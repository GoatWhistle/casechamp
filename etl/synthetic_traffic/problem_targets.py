import time

import numpy as np


def path_problem_targets(
    a,
    b,
    predecessors,
    access,
    weight,
    edge_delay,
    *,
    deadline=None,
    check=None,
):
    path = [b]
    while path[-1] != a and len(path) <= len(predecessors):
        if check:
            check()
        if deadline is not None and time.monotonic() >= deadline:
            return []
        parent = int(predecessors[path[-1]])
        if parent < 0:
            return []
        path.append(parent)
    if path[-1] != a:
        return []
    path.reverse()
    eligible = [i for i, node in enumerate(path) if node in access]
    if len(eligible) < 4:
        return []
    sampled = sorted(
        {
            eligible[int(i)]
            for i in np.linspace(0, len(eligible) - 1, min(9, len(eligible)))
        }
    )
    pairs = []
    for left, right in zip(sampled, sampled[2:]):
        u, v = path[left], path[right]
        pairs.append(
            (
                u,
                v,
                "existing_route_detour_section",
                weight,
                {
                    "target_origin": "problem_route",
                    "problem_od_source_index": a,
                    "problem_od_target_index": b,
                },
            )
        )
    hotspots = sorted(
        range(len(path) - 1),
        key=lambda i: (-edge_delay.get((path[i], path[i + 1]), 0), i),
    )[:3]
    for position in hotspots:
        delay = edge_delay.get((path[position], path[position + 1]), 0)
        if delay <= 0:
            continue
        before = [i for i in eligible if i < position]
        after = [i for i in eligible if i > position + 1]
        if before and after:
            u, v = path[before[-1]], path[after[0]]
            pairs.append(
                (
                    u,
                    v,
                    "congested_access_bypass",
                    weight,
                    {
                        "target_origin": "problem_route",
                        "problem_od_source_index": a,
                        "problem_od_target_index": b,
                        "assigned_edge_delay_vehicle_hours": delay,
                    },
                )
            )
    return pairs


def disconnected_problem_targets(a, b, access, components, coordinates, weight):
    nodes = np.asarray(sorted(access), dtype=int)
    if components[a] == components[b]:
        return []
    left = nodes[components[nodes] == components[a]]
    right = nodes[components[nodes] == components[b]]
    if not len(left) or not len(right):
        return []
    left = left[
        np.argsort(
            np.linalg.norm(coordinates[left] - coordinates[a], axis=1), kind="stable"
        )[:16]
    ]
    right = right[
        np.argsort(
            np.linalg.norm(coordinates[right] - coordinates[b], axis=1), kind="stable"
        )[:16]
    ]
    distance = np.linalg.norm(coordinates[left, None] - coordinates[right], axis=2)
    chosen = np.argsort(distance, axis=None, kind="stable")[:4]
    return [
        (
            int(left[i // len(right)]),
            int(right[i % len(right)]),
            "disconnected_demand_endpoint_vicinity_gap",
            weight,
            {
                "target_origin": "problem_gap",
                "problem_od_source_index": a,
                "problem_od_target_index": b,
            },
        )
        for i in chosen
    ]


def retain_hypothesis_provenance(target, provenance):
    if "target_origin" not in target:
        hint = next(
            (
                source
                for source in provenance
                if source.get("target_origin")
                in {"llm", "hypothesis", "agent_hypothesis"}
            ),
            None,
        )
        if hint is not None:
            target.update(hint)


def computed_edge_delay(network, hours, flow):
    edge_delay = {}
    if flow is not None:
        for u, v, value in zip(
            network.source,
            network.target,
            np.asarray(flow) * np.maximum(0, hours - network.free_hours),
            strict=True,
        ):
            key = int(u), int(v)
            edge_delay[key] = max(edge_delay.get(key, 0), float(value))
    return edge_delay


def interleave_problem_targets(rows):
    problem = [
        row
        for row in rows
        if row.get("target_origin") in {"problem_route", "problem_gap"}
    ]
    ordinary = [
        row
        for row in rows
        if row.get("target_origin") not in {"problem_route", "problem_gap"}
    ]
    result = []
    while ordinary or problem:
        if problem and (len(result) % 4 == 1 or not ordinary):
            result.append(problem.pop(0))
        elif ordinary:
            result.append(ordinary.pop(0))
    return result
