from dataclasses import replace

import numpy as np
import pytest
from synthetic_traffic.edge_identity import align_edges
from synthetic_traffic.model import Network
from synthetic_traffic.origin_flows import RemappedFlows


def network(source, target, ways):
    count = len(source)
    return Network(np.array(source), np.array(target), np.ones(count), np.ones(count),
                   np.ones(count), np.array(ways), np.arange(5), np.zeros(5), np.zeros(5),
                   np.full(count, -1))


def test_alignment_preserves_directed_parallel_identity_and_last_duplicate():
    original = network([0, 0, 1, 0], [1, 1, 0, 1], [10, 20, 10, 10])
    changed = network([1, 0, 0, 0], [0, 1, 1, 2], [10, 20, 10, 30])
    assert align_edges(original, changed, chunk_size=2).tolist() == [2, 1, 3, -1]
    with pytest.raises(ValueError):
        align_edges(original, replace(changed, raw_nodes=np.arange(5)[::-1]))


def test_chunked_alignment_matches_dictionary_oracle_for_random_reordered_edges():
    random = np.random.default_rng(42)
    for _ in range(30):
        original = network(random.integers(0, 5, 90), random.integers(0, 5, 90),
                           random.integers(-1, 20, 90))
        changed = network(random.integers(0, 5, 100), random.integers(0, 5, 100),
                          random.integers(-1, 20, 100))
        lookup = {key: index for index, key in enumerate(zip(original.source, original.target, original.way_id))}
        expected = [lookup.get(key, -1) for key in zip(changed.source, changed.target, changed.way_id)]
        assert align_edges(original, changed, chunk_size=7).tolist() == expected


def test_origin_flows_are_loaded_lazily_and_only_broken_routes_are_replaced():
    class ObservedFlows(dict):
        def __getitem__(self, key):
            accessed.append(key)
            return super().__getitem__(key)

    accessed = []
    source = ObservedFlows({10: {0: 5., 1: 0.}, 20: {1: 7.}, 30: {2: 3.}})
    mapped = RemappedFlows(np.array([2, -1, 0]), source, {20: {1: 7.}})
    assert accessed == []
    assert mapped[10] == {2: 5.}
    assert accessed == [10]
    assert mapped[20] == {1: 7.}
    assert mapped[30] == {0: 3.}
    assert source[20] == {1: 7.}
