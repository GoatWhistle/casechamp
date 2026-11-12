import numpy as np
from scipy.sparse.csgraph import connected_components, dijkstra
from scipy.spatial import cKDTree
from synthetic_traffic.assignment import route_graph
from synthetic_traffic.demand import xyz
from synthetic_traffic.model import Network
from synthetic_traffic.projects import apply_project


def generate_candidates(
    network: Network,
    flow: np.ndarray,
    hours: np.ndarray,
    ratio: np.ndarray,
    limit: int = 20,
) -> dict:
    if limit < 1 or any(len(v) != len(network.source) for v in [flow, hours, ratio]):
        raise ValueError(
            "Candidate inputs must match the network and use a positive limit"
        )
    if any(np.any(~np.isfinite(v)) or np.any(v < 0) for v in [flow, hours, ratio]):
        raise ValueError("Candidate flow/time inputs must be finite and nonnegative")
    priority = flow * np.maximum(hours - network.free_hours, 0)
    selected = np.argsort(-priority, kind="stable")
    roads = []
    seen = set()
    seeds = []
    for edge in selected:
        if flow[edge] <= 0 or priority[edge] <= 0:
            continue
        way = int(network.way_id[edge])
        if way in seen:
            continue
        seen.add(way)
        seeds.extend([int(network.source[edge]), int(network.target[edge])])
        for kind in ["capacity", "speed"]:
            project = {"kind": kind, "way_ids": [way]}
            if kind == "speed":
                project["factor"] = 1.2
            try:
                apply_project(network, project)
            except ValueError:
                continue
            roads.append(
                {
                    **project,
                    "screening_only": True,
                    "current_edge_demand_capacity_ratio": float(ratio[edge]),
                    "review": "profile_and_engineering_assumptions",
                }
            )
        if len(seen) >= limit:
            break
    if not seeds:
        return {
            "existing_corridor_projects": roads,
            "connections_for_review": [],
            "data_gaps": [],
        }
    graph, _ = route_graph(network, hours)
    _, components = connected_components(graph, directed=True, connection="strong")
    access = (
        np.searchsorted(network.raw_nodes, network.access_raw_nodes)
        if network.access_raw_nodes is not None
        else np.arange(len(network.raw_nodes))
    )
    connections = []
    gaps = []
    if len(access) == 0:
        return {
            "existing_corridor_projects": roads,
            "connections_for_review": [],
            "data_gaps": [],
        }
    coordinates = xyz(network.lat, network.lon)
    tree = cKDTree(coordinates[access])
    incident = np.isin(network.source, seeds) | np.isin(network.target, seeds)
    existing = set(
        zip(
            network.source[incident].tolist(),
            network.target[incident].tolist(),
            strict=True,
        )
    )
    pairs = set()
    for seed in dict.fromkeys(seeds):
        distance, nearby = tree.query(coordinates[seed], k=min(32, len(access)))
        times = None
        for chord, index in zip(
            np.atleast_1d(distance), np.atleast_1d(nearby), strict=True
        ):
            target = int(access[int(index)])
            pair = (min(seed, target), max(seed, target))
            if (
                seed == target
                or pair in pairs
                or (seed, target) in existing
                or (target, seed) in existing
                or not 0.1 <= chord <= 5
            ):
                continue
            pairs.add(pair)
            length = float(2 * 6371.0088 * np.arcsin(min(1.0, chord / (2 * 6371.0088))))
            if length * 1.2 > 5:
                continue
            project = {
                "kind": "connection",
                "source_node": int(network.raw_nodes[seed]),
                "target_node": int(network.raw_nodes[target]),
                "length_km": length * 1.2,
                "speed_kmh": 40,
                "length_basis": "1.2_times_geodesic_unreviewed_alignment",
                "screening_only": True,
                "review": "alignment_water_terrain_land_and_road_access_unverified",
            }
            if components[seed] != components[target]:
                if len(gaps) < limit:
                    gaps.append(
                        {
                            **project,
                            "review": "verify_possible_source_gap_before_new_road",
                        }
                    )
                continue
            if times is None:
                times = dijkstra(graph, directed=True, indices=seed)
            if times[target] <= project["length_km"] / 40:
                continue
            if len(connections) < limit:
                connections.append(
                    {
                        **project,
                        "current_between_endpoint_minutes": float(times[target] * 60),
                        "assumed_new_link_minutes": project["length_km"] / 40 * 60,
                    }
                )
        if len(connections) >= limit and len(gaps) >= limit:
            break
    return {
        "existing_corridor_projects": roads,
        "connections_for_review": connections,
        "data_gaps": gaps,
    }
