from time import monotonic

import numpy as np
import pytest
import synthetic_traffic.compiled_repair as compiled
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from synthetic_traffic.compiled_repair import repair, warmup
from synthetic_traffic.index_path_repair import changes


def test_random_directed_repairs_are_exact_and_preserve_parents():
    warmup()
    rng = np.random.default_rng(9423)
    matrix = rng.uniform(0.05, 5, (30, 30))
    matrix[rng.random((30, 30)) < 0.88] = 0
    np.fill_diagonal(matrix, 0)
    graph = csr_matrix(matrix)
    distance, parent = dijkstra(
        graph, directed=True, indices=0, return_predecessors=True
    )
    for _ in range(60):
        for _ in range(12):
            source, target = rng.choice(30, 2, replace=False)
            matrix[source, target] = rng.choice([0.0, float(rng.uniform(0.05, 5))])
        after = csr_matrix(matrix)
        touched = repair(
            after,
            after.transpose().tocsr(),
            distance,
            parent,
            changes(graph, after),
            monotonic() + 5,
        )
        np.testing.assert_allclose(distance, dijkstra(after, directed=True, indices=0))
        assert touched.dtype == np.int32
        for node in np.flatnonzero(parent >= 0):
            assert distance[node] == pytest.approx(
                distance[parent[node]] + matrix[parent[node], node]
            )
        graph = after


def test_closure_makes_unreachable_and_new_edge_restores_memmap(tmp_path):
    graph = csr_matrix(np.array([[0.0, 1.0, 0.0], [0.0, 0.0, 1.0], [0.0, 0.0, 0.0]]))
    distance, parent = dijkstra(graph, indices=0, return_predecessors=True)
    np.save(tmp_path / "distance.npy", distance)
    np.save(tmp_path / "parent.npy", parent)
    distance = np.load(tmp_path / "distance.npy", mmap_mode="c")
    parent = np.load(tmp_path / "parent.npy", mmap_mode="c")
    empty = csr_matrix((3, 3))
    touched = repair(empty, empty, distance, parent, changes(graph, empty))
    np.testing.assert_array_equal(touched, [1, 2])
    np.testing.assert_allclose(distance, [0.0, np.inf, np.inf])
    repair(graph, graph.transpose().tocsr(), distance, parent, changes(empty, graph))
    np.testing.assert_allclose(distance, [0.0, 1.0, 2.0])
    np.testing.assert_allclose(np.load(tmp_path / "distance.npy"), [0.0, 1.0, 2.0])


def test_bounded_horizon_keeps_the_existing_cutoff_semantics():
    graph = csr_matrix(np.array([[0.0, 1.0, 0.0], [1.0, 0.0, 1.0], [0.0, 1.0, 0.0]]))
    distance, parent = dijkstra(graph, indices=0, return_predecessors=True)
    changed = csr_matrix(np.array([[0.0, 3.0, 0.0], [3.0, 0.0, 1.0], [0.0, 1.0, 0.0]]))
    touched = repair(
        changed, changed, distance, parent, changes(graph, changed), horizon=1.5
    )
    np.testing.assert_array_equal(touched, [1])
    np.testing.assert_allclose(distance, [0.0, np.inf, 2.0])


def test_deadline_is_checked_inside_compiled_batches(monkeypatch):
    size = 10000
    graph = csr_matrix(
        (np.ones(size - 1), (np.arange(size - 1), np.arange(1, size))),
        shape=(size, size),
    )
    distance, parent = dijkstra(graph, indices=0, return_predecessors=True)
    weights = graph.data.copy()
    weights[0] = 2
    after = csr_matrix((weights, graph.indices, graph.indptr), shape=graph.shape)
    deadline = monotonic() + 30
    checks = []

    def clock():
        checks.append(True)
        return deadline - 1 if len(checks) == 1 else deadline + 1

    monkeypatch.setattr(compiled, "monotonic", clock)
    with pytest.raises(TimeoutError):
        repair(
            after,
            after.transpose().tocsr(),
            distance,
            parent,
            changes(graph, after),
            deadline,
        )
    assert len(checks) >= 2
