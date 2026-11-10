import numpy as np

from app.adapter.road_graph.routing import minimum_csr


def test_keeps_minimum_of_parallel_edges_in_both_directions() -> None:
    rng = np.random.default_rng(3)
    size, edges = 60, 900
    src = rng.integers(0, size, edges)
    dst = rng.integers(0, size, edges)
    weights = rng.integers(0, 20, edges).astype(np.float32) / 4
    expected: dict[tuple[int, int], float] = {}
    for a, b, w in zip(src, dst, weights, strict=True):
        for pair in ((int(a), int(b)), (int(b), int(a))):
            expected[pair] = min(expected.get(pair, np.inf), float(w))
    graph = minimum_csr(src, dst, weights, size + 5)
    assert graph.shape == (size + 5, size + 5)
    assert graph.has_sorted_indices
    assert graph.dtype == np.float64
    coo = graph.tocoo()
    actual = {
        (int(r), int(c)): float(v) for r, c, v in zip(coo.row, coo.col, coo.data, strict=True)
    }
    assert actual.keys() == expected.keys()
    assert actual == expected


def test_empty_edges_give_empty_graph() -> None:
    empty = np.array([], dtype=np.int32)
    graph = minimum_csr(empty, empty, np.array([], dtype=np.float32), 4)
    assert graph.shape == (4, 4) and graph.nnz == 0
