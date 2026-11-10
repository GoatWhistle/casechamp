from itertools import pairwise
from typing import Any

import numpy as np
from scipy.sparse.csgraph import dijkstra
from scipy.spatial import cKDTree

from app.adapter.road_graph.routing import minimum_csr

STEP_KM = 0.2
CROSS_KM = 0.15


def band_pairs(
    ids: Any, xy: Any, pairs: list[tuple[int, int]], source: int, target: int, width_km: float
) -> set[tuple[int, int]]:
    scale = float(np.cos(np.radians(np.mean(xy[:, 1]))))
    km = np.column_stack([xy[:, 0] * scale, xy[:, 1]]) * 111.195
    a = np.searchsorted(ids, [p[0] for p in pairs])
    b = np.searchsorted(ids, [p[1] for p in pairs])
    near_pairs = cKDTree(km).query_pairs(CROSS_KM, output_type="ndarray")
    sa = np.concatenate([a, near_pairs[:, 0]]) if len(near_pairs) else a
    sb = np.concatenate([b, near_pairs[:, 1]]) if len(near_pairs) else b
    length = np.maximum(np.hypot(*(km[sa] - km[sb]).T), 1e-6)
    graph = minimum_csr(sa, sb, length, len(ids))
    distance, previous = dijkstra(graph, directed=True, indices=source, return_predecessors=True)
    if not np.isfinite(distance[target]):
        return set()
    path = [target]
    while path[-1] != source:
        path.append(int(previous[path[-1]]))
    points = [km[path[0]]]
    for u, v in pairwise(path):
        steps = max(1, int(np.ceil(np.hypot(*(km[v] - km[u])) / STEP_KM)))
        points += list(km[u] + (km[v] - km[u]) * np.linspace(0, 1, steps + 1)[1:, None])
    near, _ = cKDTree(np.array(points)).query(km, distance_upper_bound=width_km + STEP_KM)
    inside = np.isfinite(near)
    return {
        (min(int(ids[i]), int(ids[j])), max(int(ids[i]), int(ids[j])))
        for i, j in zip(a, b, strict=True)
        if i != j and inside[i] and inside[j]
    }
