import numpy as np
import pytest
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import dijkstra

from app.adapter.normative.nearest_targets import nearest_targets


def test_target_approaches_can_change_the_nearest_facility() -> None:
    graph = csr_matrix(([1.0, 0.8], ([0, 0], [1, 2])), shape=(4, 4))
    costs, owners = nearest_targets(graph, [(1, 0.0), (2, 0.5)], np.array([0, 3]))
    assert costs[0] == pytest.approx(1.0)
    assert owners[0] == 0
    assert np.isinf(costs[1])
    assert owners[1] < 0


def test_direction_is_from_origin_to_facility_and_not_the_reverse() -> None:
    graph = csr_matrix(([2.0, 7.0], ([0, 1], [1, 0])), shape=(2, 2))
    costs, _ = nearest_targets(graph, [(1, 0.5)], np.array([0]))
    assert costs[0] == pytest.approx(2.5)


def test_weighted_multisource_matches_independent_searches_with_zero_edges() -> None:
    rng = np.random.default_rng(20261112)
    weights = rng.uniform(0, 10, 70)
    weights[0] = 0
    graph = csr_matrix(
        (weights, (rng.integers(0, 20, 70), rng.integers(0, 20, 70))), shape=(20, 20)
    )
    targets = [(1, 0.2), (5, 0.5), (12, 0.0), (1, 0.8)]
    costs, owners = nearest_targets(graph, targets, np.arange(20))
    reference = np.stack(
        [
            dijkstra(graph, directed=True, indices=origin)[[i for i, _ in targets]]
            + np.array([offset for _, offset in targets])
            for origin in range(20)
        ]
    )
    np.testing.assert_allclose(costs, np.min(reference, axis=1))
    for origin, owner in enumerate(owners):
        if np.isfinite(costs[origin]):
            assert reference[origin, owner] == pytest.approx(costs[origin])
