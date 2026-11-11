from itertools import pairwise

import numpy as np
import pytest
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra

from app.adapter.road_graph.bidirectional import bidirectional_path


def test_first_frontier_intersection_is_not_assumed_optimal() -> None:
    graph = csr_matrix(
        np.array(
            [
                [0, 1, 5, 0],
                [1, 0, 0, 10],
                [5, 0, 0, 5],
                [0, 10, 5, 0],
            ],
            dtype=float,
        )
    )
    result = bidirectional_path(graph, 0, 3, reverse=graph)
    assert result is not None
    assert result.nodes == [0, 2, 3]
    assert result.hours == 10


@pytest.mark.parametrize("symmetric", [False, True])
def test_seeded_graphs_match_independent_scipy_paths(symmetric: bool) -> None:
    rng = np.random.default_rng(20261111)
    for _ in range(12):
        weights = rng.uniform(0.01, 10, (30, 30))
        weights[rng.random((30, 30)) > 0.12] = 0
        np.fill_diagonal(weights, 0)
        if symmetric:
            weights += weights.T
        graph = csr_matrix(weights)
        for source, target in [(0, 29), (7, 12), (19, 2)]:
            expected = dijkstra(graph, indices=source, directed=True)[target]
            result = bidirectional_path(graph, source, target)
            if not np.isfinite(expected):
                assert result is None
                continue
            assert result is not None
            assert result.hours == pytest.approx(expected)
            assert result.nodes[0] == source and result.nodes[-1] == target
            assert sum(float(graph[a, b]) for a, b in pairwise(result.nodes)) == pytest.approx(
                expected
            )


def test_disconnected_nodes_do_not_get_an_invented_connection() -> None:
    graph = csr_matrix(np.array([[0, 1, 0], [1, 0, 0], [0, 0, 0]], dtype=float))
    assert bidirectional_path(graph, 0, 2, reverse=graph) is None
    same = bidirectional_path(graph, 1, 1)
    assert same is not None and same.nodes == [1] and same.hours == 0


def test_two_frontiers_stop_before_exploring_a_long_branch() -> None:
    rows = np.arange(9999)
    columns = rows + 1
    graph = csr_matrix((np.ones(len(rows)), (rows, columns)), shape=(10000, 10000))
    graph += graph.T
    result = bidirectional_path(graph, 0, 8, reverse=graph)
    assert result is not None
    assert result.nodes == list(range(9))
    assert result.settled_nodes < 20
