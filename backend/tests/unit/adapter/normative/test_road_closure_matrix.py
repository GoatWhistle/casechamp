import numpy as np
from scipy.sparse.csgraph import dijkstra

from app.adapter.normative.road_closure_matrix import road_closure_matrix
from app.adapter.road_graph.routing import minimum_csr


def test_closure_preserves_parallel_road_and_zero_cost_edges_without_mutating_base() -> None:
    edges = {
        "src": np.array([0, 1, 1, 2]),
        "dst": np.array([1, 0, 2, 3]),
        "h": np.array([1.0, 3.0, 0.0, 2.0]),
        "way_idx": np.array([0, 1, 2, 3]),
    }
    graph = minimum_csr(edges["src"], edges["dst"], edges["h"], 5)
    changed = road_closure_matrix(graph, edges, np.ones(4, dtype=bool), [0, 3])
    costs = dijkstra(changed, directed=True, indices=0)
    assert costs[1] == 3
    assert costs[2] == 3
    assert np.isinf(costs[3])
    np.testing.assert_allclose(dijkstra(graph, directed=True, indices=0)[:4], [0, 1, 1, 3])


def test_closure_matches_rebuilding_the_allowed_graph_for_random_parallel_roads() -> None:
    rng = np.random.default_rng(20261112)
    edges = {
        "src": rng.integers(0, 15, 100),
        "dst": rng.integers(0, 15, 100),
        "h": rng.uniform(0, 5, 100),
        "way_idx": rng.integers(0, 20, 100),
    }
    allowed = rng.random(100) > 0.2
    graph = minimum_csr(edges["src"][allowed], edges["dst"][allowed], edges["h"][allowed], 15)
    changed = road_closure_matrix(graph, edges, allowed, [1, 5, 8])
    keep = allowed & ~np.isin(edges["way_idx"], [1, 5, 8])
    rebuilt = minimum_csr(edges["src"][keep], edges["dst"][keep], edges["h"][keep], 15)
    np.testing.assert_allclose(dijkstra(changed, directed=True), dijkstra(rebuilt, directed=True))
