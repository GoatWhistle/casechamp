from collections import OrderedDict
from collections.abc import Hashable
from threading import Lock
from typing import Any

import numpy as np

from app.adapter.road_graph.road_profiles import profile_changes
from app.usecase.road_graph import RoadChange
from app.usecase.road_profile_validation import has_profile


class SearchCache:
    def __init__(self, size: int) -> None:
        self.size = size
        self.items: OrderedDict[Hashable, Any] = OrderedDict()
        self.lock = Lock()

    def get(self, key: Hashable | None) -> Any:
        if key is None:
            return None
        with self.lock:
            if key in self.items:
                self.items.move_to_end(key)
                return self.items[key]
            return None

    def put(self, key: Hashable | None, value: Any) -> None:
        if key is None:
            return
        with self.lock:
            self.items[key] = value
            self.items.move_to_end(key)
            while len(self.items) > self.size:
                self.items.popitem(last=False)


def changed_weights(
    edges: dict[str, Any],
    ways: dict[int, int],
    changes: list[RoadChange],
    profiles: dict[int, dict[str, Any]] | None = None,
) -> tuple[Any, int]:
    weights = edges["h"].copy()
    if not changes:
        return weights, 0
    if any(has_profile(change) for change in changes):
        changes, _ = profile_changes(changes, ways, profiles or {})
    factors = np.ones(int(edges["way_idx"].max()) + 1, dtype=weights.dtype)
    for change in changes:
        factors[ways[change.way_id]] = change.speed_factor
    selected = factors[edges["way_idx"]]
    mask = selected != 1
    closed = mask & (selected == 0)
    scaled = mask & ~closed
    weights[scaled] = weights[scaled] / selected[scaled]
    weights[closed] = np.inf
    touched = np.isin(edges["way_idx"], [ways[c.way_id] for c in changes])
    return weights, int(touched.sum())
