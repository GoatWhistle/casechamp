import numpy as np
import pytest
from scipy.sparse import csr_matrix

from app.adapter.road_graph.shortest_paths import ShortestPaths


def graph() -> csr_matrix:
    rng = np.random.default_rng(7)
    size, edges = 400, 1600
    src = rng.integers(0, size, edges).astype(np.int32)
    dst = rng.integers(0, size, edges).astype(np.int32)
    weights = rng.random(edges) * 5
    weights[:10] = 0.0
    return csr_matrix((weights, (src, dst)), shape=(size, size))


@pytest.mark.parametrize("limit", [np.inf, 3.0])
def test_process_pool_matches_sequential_search(limit: float) -> None:
    sources = np.array([0, 5, 17, 42, 399, 5])
    targets = np.array([1, 2, 3, 100, 250, 399, 0])
    progress: list[int] = []
    sequential = ShortestPaths().distances(graph(), sources, targets, limit, lambda _: None)
    paths = ShortestPaths(3)
    try:
        parallel = paths.distances(graph(), sources, targets, limit, progress.append)
    finally:
        paths.close()
    np.testing.assert_array_equal(parallel, sequential)
    assert sorted(progress) == list(range(1, len(sources) + 1))


def test_cancelled_progress_stops_search() -> None:
    def stop(_: int) -> None:
        raise InterruptedError()

    paths = ShortestPaths(2)
    try:
        with pytest.raises(InterruptedError):
            paths.distances(graph(), np.arange(20), np.arange(5), np.inf, stop)
    finally:
        paths.close()


@pytest.mark.parametrize("workers", [0, 49])
def test_worker_count_is_bounded(workers: int) -> None:
    with pytest.raises(ValueError):
        ShortestPaths(workers)
