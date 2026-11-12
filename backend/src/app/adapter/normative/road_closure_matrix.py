from typing import Any

import numpy as np


def road_closure_matrix(
    graph: Any, edges: dict[str, Any], allowed: Any, closed_indices: list[int]
) -> Any:
    blocked = np.isin(edges["way_idx"], closed_indices)
    affected = blocked & allowed
    count = graph.shape[0]
    left, right = edges["src"][affected], edges["dst"][affected]
    keys = np.unique(np.minimum(left, right).astype(np.int64) * count + np.maximum(left, right))
    if not len(keys):
        return graph
    best = np.full(len(keys), np.inf)
    for start in range(0, len(blocked), 1000000):
        end = start + 1000000
        keep = allowed[start:end] & ~blocked[start:end]
        a, b = edges["src"][start:end][keep], edges["dst"][start:end][keep]
        pairs = np.minimum(a, b).astype(np.int64) * count + np.maximum(a, b)
        matching = np.isin(pairs, keys)
        indices = np.searchsorted(keys, pairs[matching])
        np.minimum.at(best, indices, edges["h"][start:end][keep][matching])
    result = graph.copy()
    for key, weight in zip(keys, best, strict=True):
        a, b = divmod(int(key), count)
        for source, target in ((a, b), (b, a)):
            start, end = result.indptr[source : source + 2]
            index = int(start) + int(np.searchsorted(result.indices[start:end], target))
            if index < end and result.indices[index] == target:
                result.data[index] = weight
    return result
