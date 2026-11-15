import numpy as np
import pytest
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra
from synthetic_traffic.tree_routing import bounded_tree


def test_loaded_destination_beyond_initial_radius_does_not_expand_to_entire_country():
    graph = csr_matrix(([4.5, 100.], ([0, 1], [1, 2])), shape=(3, 3))
    tree = bounded_tree(graph, 0, [1], 4.)
    assert tree.limit == 8.
    assert tree.distance[1] == pytest.approx(4.5)
    assert np.isinf(tree.distance[2])
    assert tree.parent[1] == 0


def test_expansion_keeps_unreachable_demand_distinct_from_horizon():
    graph = csr_matrix(([4.5, 100.], ([0, 1], [1, 2])), shape=(4, 4))
    tree = bounded_tree(graph, 0, [1, 3], 4.)
    assert np.isinf(tree.limit)
    expected = dijkstra(graph, directed=True, indices=0)
    np.testing.assert_array_equal(tree.distance, expected)
    assert np.isinf(tree.distance[3])
