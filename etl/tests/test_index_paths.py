from pathlib import Path
from time import monotonic

import numpy as np
import pytest
import synthetic_traffic.index_paths as paths
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from synthetic_traffic.index_paths import DiskGraphCache


def test_random_disk_repairs_match_full_paths_and_keep_baseline(tmp_path):
    rng = np.random.default_rng(391)
    values = rng.uniform(0.1, 5, (20, 20))
    values[rng.random((20, 20)) < 0.85] = 0
    np.fill_diagonal(values, 0)
    base = DiskGraphCache(csr_matrix(values), range(20), tmp_path)
    expected_base = dijkstra(csr_matrix(values), directed=True)
    candidate = base.fork()
    try:
        for _ in range(20):
            for _ in range(7):
                u, v = rng.choice(20, 2, replace=False)
                values[u, v] = rng.choice([0.0, float(rng.uniform(0.1, 5))])
            graph = csr_matrix(values)
            candidate.update_graph(graph, monotonic() + 5)
            expected = dijkstra(graph, directed=True)
            for origin in range(20):
                np.testing.assert_allclose(
                    np.asarray(candidate.trees[origin].distance), expected[origin]
                )
                np.testing.assert_allclose(
                    candidate.trees[origin].distance[np.array([0, 3, 9, 19])],
                    expected[origin, [0, 3, 9, 19]],
                )
                np.testing.assert_allclose(
                    np.asarray(base.trees[origin].distance), expected_base[origin]
                )
    finally:
        temporary = candidate._temporary.name
        candidate.close()
    assert not Path(temporary).exists()


def test_cached_baseline_and_candidates_never_recompute_dijkstra(tmp_path, monkeypatch):
    graph = csr_matrix(np.array([[0.0, 1.0, 4.0], [0.0, 0.0, 1.0], [1.0, 0.0, 0.0]]))
    first = DiskGraphCache(graph, [0, 1], tmp_path)

    def reject(*args, **kwargs):
        raise AssertionError("Unexpected full shortest-path recomputation")

    monkeypatch.setattr(paths, "dijkstra", reject)
    reused = DiskGraphCache(graph, [0, 1], tmp_path)
    assert reused.directory == first.directory
    candidate = reused.fork()
    try:
        changed = csr_matrix(
            np.array([[0.0, 3.0, 0.4], [0.0, 0.0, 1.0], [1.0, 0.0, 0.0]])
        )
        candidate.update_graph(changed, monotonic() + 5)
        np.testing.assert_allclose(
            np.asarray(candidate.trees[0].distance), [0.0, 3.0, 0.4]
        )
        assert candidate.repaired_origins > 0
    finally:
        candidate.close()


def test_cancellation_deadline_and_disk_guard(tmp_path, monkeypatch):
    graph = csr_matrix(np.array([[0.0, 1.0], [1.0, 0.0]]))
    baseline = DiskGraphCache(graph, [0], tmp_path)
    candidate = baseline.fork()
    try:
        with pytest.raises(TimeoutError):
            candidate.update_graph(graph, monotonic() - 1)
    finally:
        candidate.close()

    def cancel():
        raise RuntimeError("Cancelled")

    with pytest.raises(RuntimeError, match="Cancelled"):
        DiskGraphCache(graph, [0], tmp_path, check=cancel)
    monkeypatch.setattr(paths, "disk_usage", lambda _: type("Usage", (), {"free": 0})())
    with pytest.raises(OSError, match="free disk"):
        DiskGraphCache(graph, [1], tmp_path)


def test_horizon_repairs_match_full_paths_with_changes_crossing_horizon(tmp_path):
    rng = np.random.default_rng(781)
    values = rng.uniform(1, 8, (24, 24))
    values[rng.random((24, 24)) < 0.90] = 0
    np.fill_diagonal(values, 0)
    baseline = DiskGraphCache(csr_matrix(values), range(24), tmp_path)
    for _ in range(12):
        changed = values.copy()
        for _ in range(8):
            u, v = rng.choice(24, 2, replace=False)
            changed[u, v] = rng.choice([0.0, float(rng.uniform(0.1, 8))])
        candidate = baseline.fork()
        try:
            graph = csr_matrix(changed)
            candidate.update_graph(graph, horizon=6)
            expected = dijkstra(graph, directed=True, limit=6)
            for origin in range(24):
                actual = np.asarray(candidate.trees[origin].distance)
                actual[actual > 6] = np.inf
                np.testing.assert_allclose(actual, expected[origin])
        finally:
            candidate.close()
