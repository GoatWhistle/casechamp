import numpy as np
import pytest
from synthetic_traffic.edge_index import EdgeIndex


def index(rows, size=6):
    ordered = sorted(rows)
    return EdgeIndex(np.array([u * size + v for u, v, _, _ in ordered]),
                     np.array([w for _, _, w, _ in ordered]),
                     np.array([i for _, _, _, i in ordered]), size)


def test_compact_edges_detect_closures_replacements_and_cost_changes():
    before = index([(0, 1, 1., 0), (1, 2, 2., 1), (2, 3, 3., 2), (3, 4, 4., 3)])
    after = index([(0, 1, 1., 0), (1, 2, 2., 9), (2, 3, 4., 2), (4, 5, 1., 4)])
    assert before.changed(after) == {(1, 2), (2, 3), (3, 4), (4, 5)}
    assert before.changed(before) == set()
    assert dict(before) == {(0, 1): (1., 0), (1, 2): (2., 1), (2, 3): (3., 2), (3, 4): (4., 3)}
    with pytest.raises(KeyError):
        _ = before[5, 0]


def test_compact_adjacency_preserves_direction_and_weights():
    edges = index([(0, 1, 1., 0), (1, 2, 2., 1), (3, 1, 3., 2)])
    incoming, outgoing = edges.adjacency()
    assert list(incoming.get(1)) == [(0, 1.), (3, 3.)]
    assert list(outgoing.get(1)) == [(2, 2.)]
    assert list(outgoing.get(5)) == []


def test_batch_lookup_preserves_order_repetition_and_rejects_absent_edges():
    selected = index([(0, 1, 1., 7), (2, 0, 2., 3)], size=3)
    assert selected.edge_ids([(2, 0), (0, 1), (2, 0)]).tolist() == [3, 7, 3]
    assert selected.edge_ids([]).tolist() == []
    with pytest.raises(KeyError):
        selected.edge_ids([(0, 1), (1, 2)])
