from dataclasses import dataclass

import numpy as np
from synthetic_traffic.edge_index import EdgeIndex


@dataclass(frozen=True)
class EdgeChanges:
    increased_source: np.ndarray
    increased_target: np.ndarray
    decreased_source: np.ndarray
    decreased_target: np.ndarray
    decreased_weight: np.ndarray

    def affected(self, tree):
        invalid = self.increased_target[
            tree.parent[self.increased_target] == self.increased_source
        ]
        improved = (
            tree.distance[self.decreased_source] + self.decreased_weight
            < tree.distance[self.decreased_target]
        )
        return set(invalid.tolist()), list(zip(
            self.decreased_source[improved].tolist(),
            self.decreased_target[improved].tolist(),
            self.decreased_weight[improved].tolist(), strict=True,
        ))


def edge_changes(old, new):
    if isinstance(old, EdgeIndex) and isinstance(new, EdgeIndex):
        if old.size != new.size:
            raise ValueError('Edge indexes must preserve node count')
        keys = np.union1d(old.keys_array, new.keys_array)
        before = _weights(old, keys)
        after = _weights(new, keys)
        source, target = keys // old.size, keys % old.size
    else:
        pairs = sorted(old.keys() | new.keys())
        source = np.array([u for u, _ in pairs], dtype=np.int64)
        target = np.array([v for _, v in pairs], dtype=np.int64)
        before = np.array([old.get(pair, (np.inf, -1))[0] for pair in pairs])
        after = np.array([new.get(pair, (np.inf, -1))[0] for pair in pairs])
    increased, decreased = after > before, after < before
    return EdgeChanges(source[increased], target[increased],
                       source[decreased], target[decreased], after[decreased])


def _weights(index, keys):
    positions = np.searchsorted(index.keys_array, keys)
    present = positions < len(index)
    present[present] &= index.keys_array[positions[present]] == keys[present]
    weights = np.full(len(keys), np.inf)
    weights[present] = index.weights[positions[present]]
    return weights
