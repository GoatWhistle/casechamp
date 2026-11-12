from pathlib import Path
from time import monotonic
from types import SimpleNamespace
from typing import Any, cast

import numpy as np
import pytest
from scipy.sparse import csr_matrix
from synthetic_traffic.index_paths import DiskGraphCache
from synthetic_traffic.model import Network

from app.adapter.traffic.index_delta import IndexDelta
from app.adapter.traffic.index_targets import index_route_targets


class TinyIndex:
    def __init__(
        self, directory: Path, market: int = 4, hours: float = 1, modern: bool = True
    ) -> None:
        graph = csr_matrix(
            (
                np.full(8, hours),
                (np.array([0, 1, 2, 3, 1, 2, 3, 4]), np.array([1, 2, 3, 4, 0, 1, 2, 3])),
            ),
            shape=(5, 5),
        )
        self.cache = DiskGraphCache(graph, [market], directory)
        self.modern = modern
        self.cities = [("market", market, 0.2, 200.0, "market-point")]
        self.regions = [
            SimpleNamespace(
                nodes=np.array([0]),
                snaps=np.array([0.1]),
                population=np.array([100]),
                point_ids=["origin"],
            )
        ]

    def distances(self, cache: DiskGraphCache, origin: int, targets: Any) -> Any:
        values = np.array(cache.trees[origin].distance[targets], copy=True)
        if not self.modern:
            values[values > 72] = np.inf
        return values


def local_network(straight: bool = False) -> Network:
    return Network(
        source=np.array([0, 1, 2]),
        target=np.array([1, 2, 3]),
        free_hours=np.ones(3),
        capacity=np.ones(3),
        length_km=np.ones(3),
        way_id=np.arange(3),
        raw_nodes=np.arange(4),
        lat=np.zeros(4) if straight else np.array([0.0, 1.0, 1.0, 0.0]),
        lon=np.array([0.0, 0.3, 0.6, 1.0]) if straight else np.array([0.0, 0.0, 1.0, 1.0]),
        shared=np.full(3, -1),
    )


def test_index_targets_follow_market_path_to_local_gateway(tmp_path: Path) -> None:
    cache = TinyIndex(tmp_path)
    result = index_route_targets(
        cast(IndexDelta, cache), local_network(), monotonic() + 5, lambda: None
    )
    assert len(result) == 1
    row = result[0]
    assert (row["source_node"], row["target_node"]) == (0, 3)
    assert row["origin"] == "index_route" and row["screening_only"] is True
    assert row["estimated_baseline_hours"] == pytest.approx(4.3)
    expected = (
        100
        * 200
        * (np.exp(-np.log(2) / 2 * row["estimated_direct_hours"]) - np.exp(-np.log(2) / 2 * 4.3))
    )
    assert row["priority"] == pytest.approx(expected)
    assert row["priority"] > 0


def test_entire_market_route_inside_window_uses_market(tmp_path: Path) -> None:
    cache = TinyIndex(tmp_path, market=3)
    result = index_route_targets(
        cast(IndexDelta, cache), local_network(), monotonic() + 5, lambda: None
    )
    assert result[0]["target_node"] == 3
    assert result[0]["estimated_baseline_hours"] == pytest.approx(3.3)


def test_straight_route_and_legacy_unreachable_markets_are_not_targets(tmp_path: Path) -> None:
    cache = TinyIndex(tmp_path)
    assert (
        index_route_targets(
            cast(IndexDelta, cache), local_network(True), monotonic() + 5, lambda: None
        )
        == []
    )
    legacy = TinyIndex(tmp_path, hours=25, modern=False)
    assert (
        index_route_targets(
            cast(IndexDelta, legacy), local_network(), monotonic() + 5, lambda: None
        )
        == []
    )


def test_parent_maps_open_once_per_market_and_pairs_are_deduplicated(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    cache = TinyIndex(tmp_path)
    cache.cities.append(("other", 4, 0.2, 50.0, "other-point"))
    original = np.load
    opened = []

    def load(path: Any, *args: Any, **kwargs: Any) -> Any:
        if str(path).endswith("-parent.npy"):
            opened.append(path)
        return original(path, *args, **kwargs)

    monkeypatch.setattr(np, "load", load)
    result = index_route_targets(
        cast(IndexDelta, cache), local_network(), monotonic() + 5, lambda: None
    )
    assert len(result) == 1 and len(opened) == 1


def test_deadline_and_cancellation_stop_target_generation(tmp_path: Path) -> None:
    cache = TinyIndex(tmp_path)
    assert (
        index_route_targets(cast(IndexDelta, cache), local_network(), monotonic() - 1, lambda: None)
        == []
    )

    def cancel() -> None:
        raise RuntimeError("Cancelled")

    with pytest.raises(RuntimeError, match="Cancelled"):
        index_route_targets(cast(IndexDelta, cache), local_network(), monotonic() + 5, cancel)
