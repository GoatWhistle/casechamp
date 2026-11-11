import numpy as np

from app.adapter.road_graph.search_cache import SearchCache, changed_weights
from app.usecase.road_graph import RoadChange


def test_vectorized_changes_match_per_way_loop() -> None:
    rng = np.random.default_rng(5)
    edges = {
        "h": rng.random(500).astype(np.float32) + 0.1,
        "way_idx": rng.integers(0, 40, 500),
    }
    changes = [RoadChange(100 + w, f) for w, f in [(3, 0.0), (7, 1.2), (9, 0.5), (11, 1.0)]]
    ways = {c.way_id: c.way_id - 100 for c in changes}
    expected = edges["h"].copy()
    count = 0
    for change in changes:
        mask = edges["way_idx"] == ways[change.way_id]
        count += int(mask.sum())
        expected[mask] = expected[mask] / change.speed_factor if change.speed_factor else np.inf
    weights, changed = changed_weights(edges, ways, changes)
    assert weights.dtype == np.float32
    np.testing.assert_array_equal(weights, expected)
    assert changed == count


def test_cache_keeps_recent_scenarios_and_skips_unkeyed() -> None:
    cache = SearchCache(2)
    cache.put(None, 1)
    cache.put("a", 1)
    cache.put("b", 2)
    assert cache.get("a") == 1
    cache.put("c", 3)
    assert cache.get("b") is None and cache.get("a") == 1 and cache.get(None) is None
