from dataclasses import replace

import numpy as np
from scipy.sparse.csgraph import dijkstra
from synthetic_traffic.assignment import route_graph
from synthetic_traffic.edge_changes import edge_changes
from synthetic_traffic.edge_index import EdgeIndex
from synthetic_traffic.incremental_paths import PathCache
from synthetic_traffic.model import Network, Trip
from synthetic_traffic.tree_store import Tree


def test_many_origins_do_not_repeat_scalar_edge_searches(monkeypatch):
    size = 80
    source = np.arange(size - 1)
    graph = Network(source=source, target=source + 1, free_hours=np.ones(size - 1),
                    capacity=np.full(size - 1, 10.), length_km=np.ones(size - 1),
                    way_id=source, raw_nodes=np.arange(size), lat=np.zeros(size),
                    lon=np.zeros(size), shared=np.full(size - 1, -1))
    trips = [Trip(origin, size - 1, 1.) for origin in range(20)]
    paths = PathCache(graph, trips, graph.free_hours, path_limit=100.)
    changed = replace(graph, free_hours=graph.free_hours * 1.1)
    calls = 0
    original = EdgeIndex.__getitem__

    def count(self, pair):
        nonlocal calls
        calls += 1
        return original(self, pair)

    monkeypatch.setattr(EdgeIndex, '__getitem__', count)
    paths.update(changed, changed.free_hours)
    matrix, _ = route_graph(changed, changed.free_hours)
    for origin in paths.entries:
        expected = dijkstra(matrix, directed=True, indices=origin)
        np.testing.assert_allclose(paths.trees[origin].distance, expected)
    assert calls < len(source), f'{calls} scalar searches for {len(trips)} origins'


def test_change_classification_matches_scalar_rules_with_additions_and_removals():
    rng = np.random.default_rng(42)
    size = 100
    for _ in range(30):
        old_keys = np.sort(rng.choice(size * size, 300, replace=False))
        new_keys = np.sort(rng.choice(size * size, 300, replace=False))
        old = EdgeIndex(old_keys, rng.uniform(.1, 3, len(old_keys)), np.arange(300), size)
        new = EdgeIndex(new_keys, rng.uniform(.1, 3, len(new_keys)), np.arange(300), size)
        parent = rng.integers(-1, size, size)
        distance = rng.uniform(0, 10, size)
        distance[rng.random(size) < .2] = np.inf
        tree = Tree(distance, parent)
        changed = old.changed(new)
        expected_invalid = {v for u, v in changed if parent[v] == u and (u, v) in old
                            and ((u, v) not in new or new[u, v][0] > old[u, v][0])}
        expected_improved = {(u, v, new[u, v][0]) for u, v in changed if (u, v) in new
                             and ((u, v) not in old or new[u, v][0] < old[u, v][0])
                             and distance[u] + new[u, v][0] < distance[v]}
        invalid, improved = edge_changes(old, new).affected(tree)
        assert invalid == expected_invalid
        assert set(improved) == expected_improved
