from time import monotonic

import numpy as np
import pytest
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from synthetic_traffic import index_paths
from synthetic_traffic.compiled_repair import repair
from synthetic_traffic.index_paths import DiskGraphCache


def delta(source, target, old, new):
    return (
        np.array(source, dtype=np.int64),
        np.array(target, dtype=np.int64),
        np.array(old, dtype=float),
        np.array(new, dtype=float),
    )


def matrix():
    return np.array([[0.0, 1, 5, 0], [0, 0, 1, 0], [0, 0, 0, 0], [0, 0, 0, 0]])


def test_sparse_delta_skips_full_scan_unaffected_trees_and_reverse(
    tmp_path, monkeypatch
):
    values = matrix()
    baseline = DiskGraphCache(csr_matrix(values), range(4), tmp_path)
    candidate = baseline.fork()
    values[1, 2] = 0.5
    touched = []
    writable = index_paths.DiskTree.writable

    def write(tree):
        touched.append(tree.origin)
        return writable(tree)

    def reject(*args, **kwargs):
        raise AssertionError("Unexpected full graph scan or transpose")

    monkeypatch.setattr(index_paths, "changes", reject)
    monkeypatch.setattr(index_paths.DiskTree, "writable", write)
    monkeypatch.setattr(csr_matrix, "transpose", reject)
    try:
        candidate.update_graph(csr_matrix(values), delta=delta([1], [2], [1], [0.5]))
        assert touched == [0, 1]
        assert candidate.considered_origins == 4
        assert candidate.skipped_origins == 2
        assert candidate.last_update_timings["affected_origins"] == 2
        assert candidate.trees[2].overlay is None
        assert candidate.trees[0].overlay is not None
        np.testing.assert_allclose(
            np.asarray(candidate.trees[0].distance), [0, 1, 1.5, np.inf]
        )
    finally:
        candidate.close()


@pytest.mark.parametrize("old,new", [(5, 4), (5, 6)])
def test_nonimproving_change_and_unused_increase_do_not_open_writable_trees(
    tmp_path, monkeypatch, old, new
):
    values = matrix()
    baseline = DiskGraphCache(csr_matrix(values), range(4), tmp_path)
    candidate = baseline.fork()
    values[0, 2] = new
    monkeypatch.setattr(
        index_paths.DiskTree,
        "writable",
        lambda tree: pytest.fail("Unchanged market opened writable"),
    )
    try:
        candidate.update_graph(csr_matrix(values), delta=delta([0], [2], [old], [new]))
        assert candidate.skipped_origins == 4
        assert candidate.repaired_origins == 0
        assert candidate.last_update_timings["affected_origins"] == 0
    finally:
        candidate.close()


def test_increased_parent_edge_repairs_exactly_and_keeps_sparse_overlay(tmp_path):
    values = matrix()
    baseline = DiskGraphCache(csr_matrix(values), range(4), tmp_path)
    candidate = baseline.fork()
    values[0, 1] = 4
    graph = csr_matrix(values)
    try:
        candidate.update_graph(graph, delta=delta([0], [1], [1], [4]))
        for origin in range(4):
            np.testing.assert_allclose(
                np.asarray(candidate.trees[origin].distance),
                dijkstra(graph, indices=origin),
            )
        overlay = candidate.trees[0].overlay
        assert overlay is not None
        nodes = np.load(overlay / "nodes.npy")
        assert np.all(nodes[:-1] < nodes[1:])
        np.testing.assert_allclose(
            np.load(overlay / "distance.npy"), dijkstra(graph, indices=0)[nodes]
        )
    finally:
        candidate.close()


@pytest.mark.parametrize("new,affected", [(80, False), (60, True)])
def test_sparse_prefilter_preserves_conservative_72_hour_horizon(
    tmp_path, new, affected
):
    graph = csr_matrix(np.array([[0.0, 100], [0, 0]]))
    baseline = DiskGraphCache(graph, [0], tmp_path)
    candidate = baseline.fork()
    try:
        changed = csr_matrix(np.array([[0.0, new], [0, 0]]))
        candidate.update_graph(changed, horizon=72, delta=delta([0], [1], [100], [new]))
        assert bool(candidate.repaired_origins) is affected
        actual = np.asarray(candidate.trees[0].distance)
        actual[actual > 72] = np.inf
        np.testing.assert_allclose(actual, dijkstra(changed, indices=0, limit=72))
    finally:
        candidate.close()


def test_sparse_delta_validates_pairs_without_trusting_wrong_old_weights(tmp_path):
    values = matrix()
    baseline = DiskGraphCache(csr_matrix(values), [0], tmp_path)
    candidate = baseline.fork()
    values[0, 1] = 2
    try:
        with pytest.raises(ValueError, match="do not match"):
            candidate.update_graph(csr_matrix(values), delta=delta([0], [1], [99], [2]))
        with pytest.raises(ValueError, match="once"):
            candidate.update_graph(
                csr_matrix(values), delta=delta([0, 0], [1, 1], [1, 1], [2, 2])
            )
        with pytest.raises(TimeoutError):
            candidate.update_graph(
                csr_matrix(values),
                deadline=monotonic() - 1,
                delta=delta([0], [1], [1], [2]),
            )
    finally:
        candidate.close()


def test_compiled_decrease_needs_no_reverse_but_parent_increase_does():
    graph = csr_matrix(matrix())
    distance, parent = dijkstra(graph, indices=0, return_predecessors=True)
    values = matrix()
    values[1, 2] = 0.5
    after = csr_matrix(values)
    repair(after, None, distance, parent, delta([1], [2], [1], [0.5]))
    np.testing.assert_allclose(distance, dijkstra(after, indices=0))
    values[0, 1] = 2
    with pytest.raises(ValueError, match="reverse graph"):
        repair(csr_matrix(values), None, distance, parent, delta([0], [1], [1], [2]))
