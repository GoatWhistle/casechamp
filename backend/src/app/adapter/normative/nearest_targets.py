from typing import Any

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra


def nearest_targets(graph: Any, targets: list[tuple[int, float]], origins: Any) -> tuple[Any, Any]:
    count = graph.shape[0]
    reverse = graph.transpose().tocsr()
    weights = np.array([entry[1] for entry in targets], dtype=np.float64)
    nodes = np.array([entry[0] for entry in targets], dtype=np.int32)
    matrix = csr_matrix(
        (
            np.concatenate((reverse.data, weights)),
            np.concatenate((reverse.indices, nodes)),
            np.concatenate(
                (reverse.indptr, reverse.nnz + np.arange(1, len(targets) + 1, dtype=np.int32))
            ),
        ),
        shape=(count + len(targets), count + len(targets)),
    )
    del reverse
    distances, _, sources = dijkstra(
        matrix,
        directed=True,
        indices=np.arange(count, count + len(targets), dtype=np.int32),
        min_only=True,
        return_predecessors=True,
    )
    return distances[origins], sources[origins] - count
