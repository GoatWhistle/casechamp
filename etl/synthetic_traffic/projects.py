from dataclasses import replace

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
from synthetic_traffic.demand import xyz
from synthetic_traffic.model import Network


def apply_project(network: Network, project: dict) -> Network:
    kind = project.get("kind")
    if kind == "connection":
        nodes = [int(project["source_node"]), int(project["target_node"])]
        positions = np.searchsorted(network.raw_nodes, nodes)
        if np.any(positions >= len(network.raw_nodes)) or not np.array_equal(
            network.raw_nodes[positions], nodes
        ):
            raise ValueError("New connection endpoints are absent from the network")
        a, b = map(int, positions)
        length = float(project["length_km"])
        speed = float(project.get("speed_kmh", 40))
        coords = xyz(network.lat[positions], network.lon[positions])
        chord = float(np.linalg.norm(coords[0] - coords[1]))
        distance = 2 * 6371.0088 * np.arcsin(min(1, chord / (2 * 6371.0088)))
        if a == b or not np.isfinite(length) or not distance <= length <= 5:
            raise ValueError(
                "Connection must be at least its geodesic distance and at most 5 km"
            )
        if not np.isfinite(speed) or not 0 < speed <= 60:
            raise ValueError("Local connection speed must be in (0,60] km/h")
        return replace(
            network,
            source=np.r_[network.source, a, b],
            target=np.r_[network.target, b, a],
            free_hours=np.r_[network.free_hours, length / speed, length / speed],
            capacity=np.r_[network.capacity, 1800.0, 1800.0],
            length_km=np.r_[network.length_km, length, length],
            way_id=np.r_[network.way_id, -1, -1],
            shared=np.r_[network.shared, -1, -1],
        )
    ways = project.get("way_ids", [])
    if not ways or any(isinstance(w, bool) or not isinstance(w, int) for w in ways):
        raise ValueError("Project needs integer way_ids")
    selected = np.isin(network.way_id, ways)
    if set(ways) != set(network.way_id[selected].tolist()):
        raise ValueError("Project contains absent road identifiers")
    pairs = np.column_stack(
        (
            network.way_id[selected],
            np.minimum(network.source[selected], network.target[selected]),
            np.maximum(network.source[selected], network.target[selected]),
        )
    )
    _, unique = np.unique(pairs, axis=0, return_index=True)
    length = float(network.length_km[selected][unique].sum())
    nodes = np.unique(np.r_[network.source[selected], network.target[selected]])
    graph = csr_matrix(
        (
            np.ones(selected.sum()),
            (
                np.searchsorted(nodes, network.source[selected]),
                np.searchsorted(nodes, network.target[selected]),
            ),
        ),
        shape=(len(nodes), len(nodes)),
    )
    if connected_components(graph, directed=False, return_labels=False) != 1:
        raise ValueError("An improvement project must cover a contiguous corridor")
    if kind == "speed":
        factor = float(project.get("factor", 1.2))
        if not np.isfinite(factor) or not 1 < factor <= 1.3 or length > 30:
            raise ValueError(
                "Speed project is limited to +30% and 30 km of existing roads"
            )
        hours = network.free_hours.copy()
        hours[selected] /= factor
        return replace(network, free_hours=hours)
    if kind == "capacity":
        if (
            project.get("extra_lanes", 1) != 1
            or length > 10
            or np.any(network.capacity[selected] > 1800)
            or np.any(network.shared[selected] >= 0)
        ):
            raise ValueError(
                "Capacity project needs <=10 km, one extra lane/direction and no shared lane"
            )
        capacity = network.capacity.copy()
        capacity[selected] += 1800
        return replace(network, capacity=capacity)
    raise ValueError("Project kind must be speed, capacity or connection")
