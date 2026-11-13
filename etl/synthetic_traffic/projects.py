from dataclasses import replace

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
from synthetic_traffic.model import Network
from synthetic_traffic.lane_closure import close_lane


def apply_project(network: Network, project: dict) -> Network:
    kind = project.get("kind")
    if kind not in {"capacity", "closure", "lane_closure"}:
        raise ValueError("Project kind must be capacity, closure or lane_closure")
    ways = project.get("way_ids", [])
    if not ways or any(isinstance(w, bool) or not isinstance(w, int) for w in ways):
        raise ValueError("Project needs integer way_ids")
    selected = np.isin(network.way_id, ways)
    edge_indices = project.get("edge_indices")
    if edge_indices is not None:
        if not edge_indices or any(isinstance(i, bool) or not isinstance(i, int) or i < 0 or i >= len(selected) for i in edge_indices):
            raise ValueError("Project needs valid baseline edge indices")
        limited = np.zeros(len(selected), dtype=bool)
        limited[edge_indices] = True
        if np.any(limited & ~selected):
            raise ValueError("Project edges must belong to selected roads")
        selected &= limited
    if set(ways) != set(network.way_id[selected].tolist()):
        raise ValueError("Project contains absent road identifiers")
    if kind == "lane_closure":
        return close_lane(network, selected)
    if kind == "closure":
        keep = ~selected
        if not keep.any():
            raise ValueError("Closure cannot remove every network edge")
        return replace(
            network,
            **{
                key: getattr(network, key)[keep]
                for key in (
                    "source",
                    "target",
                    "free_hours",
                    "capacity",
                    "length_km",
                    "way_id",
                    "shared",
                )
            },
        )
    if corridor_parts(network, np.flatnonzero(selected)) != 1:
        raise ValueError("An improvement project must cover a contiguous corridor")
    if kind == "capacity":
        lanes = project.get("extra_lanes", 1)
        if (
            isinstance(lanes, bool)
            or not isinstance(lanes, int)
            or not 1 <= lanes <= 5
            or np.any(network.shared[selected] >= 0)
        ):
            raise ValueError(
                "Capacity project requires 1 to 5 extra lanes and no shared lane"
            )
        capacity = network.capacity.copy()
        capacity[selected] += 1800 * lanes
        return replace(network, capacity=capacity)
    raise ValueError(
        "Project kind must be capacity, closure or lane_closure"
    )


def corridor_parts(network: Network, edges: list[int] | np.ndarray) -> int:
    source, target = network.source[edges], network.target[edges]
    nodes = np.unique(np.r_[source, target])
    graph = csr_matrix((np.ones(len(edges)), (np.searchsorted(nodes, source),
                                            np.searchsorted(nodes, target))),
                       shape=(len(nodes), len(nodes)))
    return int(connected_components(graph, directed=False, return_labels=False))
