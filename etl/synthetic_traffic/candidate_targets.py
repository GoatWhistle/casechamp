import time
from itertools import combinations

import numpy as np
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree
from synthetic_traffic.assignment import route_graph
from synthetic_traffic.demand import xyz
from synthetic_traffic.hypothesis_targets import diversify_targets, prepare_hypotheses
from synthetic_traffic.model import Network
from synthetic_traffic.problem_targets import (
    computed_edge_delay,
    disconnected_problem_targets,
    interleave_problem_targets,
    path_problem_targets,
    retain_hypothesis_provenance,
)


def rank_targets(
    network: Network,
    hours: np.ndarray,
    access: np.ndarray,
    components: np.ndarray,
    *,
    flow=None,
    trips=None,
    zones=None,
    hypotheses=None,
    geography_groups=None,
    deadline=None,
    check=None,
    limit=512,
    diagnostics=None,
) -> list[dict]:
    access = np.asarray(access, dtype=int)
    allowed = set(map(int, access))
    proposed, hypothesis_diagnostics = prepare_hypotheses(
        network,
        access,
        hypotheses,
        geography_groups,
        deadline,
        check,
    )
    if not len(access):
        if diagnostics is not None:
            diagnostics.update(hypothesis_diagnostics)
            diagnostics.update({"eligible_targets": 0, "dijkstra_origins": 0})
        return []
    coordinates = xyz(network.lat, network.lon)
    tree = cKDTree(coordinates[access])
    population = {}
    for zone in zones or []:
        population[zone.node] = population.get(zone.node, 0.0) + max(0, zone.population)
    mean_population = float(np.mean(list(population.values()))) if population else 1.0
    attached = {}

    def attach(node):
        if node in allowed:
            return node
        if node not in attached:
            attached[node] = int(access[int(tree.query(coordinates[node])[1])])
        return attached[node]

    for trip in trips or []:
        a, b = attach(trip.origin), attach(trip.destination)
        weight = (
            trip.vehicles_per_hour
            * np.sqrt(
                population.get(trip.origin, 1.0) * population.get(trip.destination, 1.0)
            )
            / mean_population
        )
        proposed.append((a, b, "fixed_od_detour", float(weight), {}))
    zone_nodes = sorted(population, key=lambda node: (-population[node], node))[:64]
    for a, b in combinations(zone_nodes, 2):
        if components[a] != components[b]:
            proposed.append(
                (
                    attach(a),
                    attach(b),
                    "population_connection_gap",
                    float(np.sqrt(population[a] * population[b])),
                    {},
                )
            )
    if not trips:
        demand = np.zeros(len(network.raw_nodes))
        if flow is not None:
            demand += np.bincount(network.source, weights=flow, minlength=len(demand))
            demand += np.bincount(network.target, weights=flow, minlength=len(demand))
        anchors = sorted(
            access.tolist(),
            key=lambda node: (-population.get(node, 0), -demand[node], node),
        )[:32]
        sampled = access[:: max(1, len(access) // 64)].tolist()
        for a in anchors:
            for b in sampled:
                proposed.append(
                    (
                        a,
                        b,
                        "network_detour_screen",
                        float(max(1.0, demand[a] + demand[b])),
                        {},
                    )
                )
    counts = {
        "proposed_pairs": len(proposed),
        "hypotheses": len(hypotheses or []),
        **hypothesis_diagnostics,
        "existing_or_same_endpoint": 0,
        "geography_rejected": 0,
        "no_optimistic_gain": 0,
        "origin_budget_skipped": 0,
    }
    graph, _ = route_graph(network, hours)
    existing = set(zip(network.source.tolist(), network.target.tolist()))
    cache = {}
    parents = {}
    problem_paths = 0
    problem_pairs = 0
    edge_delay = computed_edge_delay(network, hours, flow)
    targets = {}
    proposed.sort(
        key=lambda row: (
            -int(row[4].get("target_origin") == "index_route"),
            -row[4].get("target_priority", 0)
            if row[4].get("target_origin") == "index_route"
            else 0,
            -int(components[row[0]] != components[row[1]]),
            -row[3],
            row[0],
            row[1],
        )
    )
    for position, (a, b, reason, weight, metadata) in enumerate(proposed):
        if check:
            check()
        if deadline is not None and time.monotonic() >= deadline:
            break
        if a == b or (a, b) in existing or (b, a) in existing:
            counts["existing_or_same_endpoint"] += 1
            continue
        if geography_groups and geography_groups[a] != geography_groups[b]:
            counts["geography_rejected"] += 1
            continue
        if a not in cache:
            if len(cache) >= 128:
                counts["origin_budget_skipped"] += 1
                continue
            cache[a], parents[a] = dijkstra(
                graph, directed=True, indices=a, return_predecessors=True
            )
        current = float(cache[a][b])
        if reason == "fixed_od_detour" and problem_paths < 64:
            problem_paths += 1
            seeds = (
                path_problem_targets(
                    a,
                    b,
                    parents[a],
                    allowed,
                    weight,
                    edge_delay,
                    deadline=deadline,
                    check=check,
                )
                if np.isfinite(current)
                else disconnected_problem_targets(
                    a, b, allowed, components, coordinates, weight
                )
            )
            proposed[position + 1 : position + 1] = seeds
            problem_pairs += len(seeds)
        chord = float(np.linalg.norm(coordinates[a] - coordinates[b]))
        distance = float(12742.0176 * np.arcsin(min(1.0, chord / 12742.0176)))
        if distance <= 0:
            continue
        optimistic_hours = distance / 60
        disconnected = not np.isfinite(current)
        saving = None if disconnected else max(0.0, current - optimistic_hours)
        if not disconnected and saving <= 0:
            counts["no_optimistic_gain"] += 1
            continue
        score = weight if disconnected else weight * saving
        target = {
            **metadata,
            "source_index": a,
            "target_index": b,
            "target_reason": "disconnected_" + reason if disconnected else reason,
            "potential_score": score,
            "potential_weight": weight,
            "current_between_endpoint_minutes": None if disconnected else current * 60,
            "optimistic_geodesic_link_minutes": optimistic_hours * 60,
            "potential_time_saving_minutes": None if saving is None else saving * 60,
            "disconnected": disconnected,
            "potential_basis": "screening_only_geodesic_at_60_kmh_not_verified_effect",
        }
        key = min(a, b), max(a, b)
        previous = targets.get(key)
        provenance = [
            {**metadata, "target_origin": metadata.get("target_origin", reason)}
        ]
        if previous is not None:
            provenance = previous.get("source_provenance", []) + provenance
        if (
            previous is None
            or (
                metadata.get("target_origin") == "index_route"
                and previous.get("target_origin") != "index_route"
            )
            or (
                previous.get("target_origin") != "index_route"
                and score > previous["potential_score"]
            )
        ):
            targets[key] = target
        targets[key]["source_provenance"] = provenance
        retain_hypothesis_provenance(targets[key], provenance)
    values = list(targets.values())
    if diagnostics is not None:
        diagnostics.update(counts)
        diagnostics.update(
            {
                "problem_paths_screened": problem_paths,
                "problem_section_pairs": problem_pairs,
                "dijkstra_origins": len(cache),
                "eligible_targets": len(targets),
                "disconnected_targets": sum(t["disconnected"] for t in values),
                "index_route_targets": sum(
                    t.get("target_origin") == "index_route" for t in values
                ),
            }
        )
    ranked = sorted(
        targets.values(),
        key=lambda row: (
            -int(row.get("target_origin") == "index_route"),
            -row.get("target_priority", 0)
            if row.get("target_origin") == "index_route"
            else 0,
            -int(row["disconnected"]),
            -row["potential_score"],
            row["source_index"],
            row["target_index"],
        ),
    )
    return diversify_targets(interleave_problem_targets(ranked), limit, diagnostics)
