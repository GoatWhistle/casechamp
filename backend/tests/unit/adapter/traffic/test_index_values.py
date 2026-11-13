from pathlib import Path
from types import SimpleNamespace
from typing import Any

import numpy as np
import pytest
from scipy.sparse.csgraph import floyd_warshall

from app.adapter.traffic.index_delta import RegionOrigins
from app.adapter.traffic.index_values import IndexValues, PopulationGroup


class Owner:
    def __init__(self, modern: bool = True) -> None:
        self.population_groups: list[PopulationGroup] = []
        self.modern = modern
        self.cities = [
            ("a", 0, 0.1, 30.0, "a-id"),
            ("b", 3, 0.2, 80.0, "b-id"),
            ("c", 6, 0.3, 100.0, "c-id"),
        ]
        self.trunk: list[Any] = []
        self.norm = 175.0
        self.regions = [
            RegionOrigins(
                "A",
                np.array([1, 2]),
                np.array([0.4, 0.6]),
                np.array([40, 60]),
                100,
                2,
                ["one", "two"],
            ),
            RegionOrigins(
                "B",
                np.array([4, 5]),
                np.array([0.5, 0.7]),
                np.array([20, 80]),
                100,
                2,
                ["b-id", "five"],
            ),
        ]
        self.raw = np.abs(np.array([0, 3, 6])[:, None] - np.arange(8)[None, :]).astype(float)
        self.reads = 0

    def distances(self, cache: Any, origin: int, targets: Any) -> Any:
        self.reads += 1
        values = self.raw[[0, 3, 6].index(origin), targets].copy()
        if not self.modern:
            values[values > 72] = np.inf
        return values


def oracle(owner: Owner, raw: Any) -> list[float]:
    raw = raw.copy()
    if not owner.modern:
        raw[raw > 72] = np.inf
    city_nodes = np.array([c[1] for c in owner.cities])
    snaps = np.array([c[2] for c in owner.cities])
    city_road = raw[:, city_nodes] + snaps + snaps[:, None]
    indices = {c[0]: i for i, c in enumerate(owner.cities)}
    for source, target, mode, hours in owner.trunk:
        a, b = indices[source], indices[target]
        city_road[a, b] = min(city_road[a, b], hours + (1 if mode == "rail" else 2.5))
    np.fill_diagonal(city_road, 0)
    transfers = floyd_warshall(np.ascontiguousarray(city_road))
    result = []
    for region in owner.regions:
        road = np.array(
            [
                raw[j, region.nodes].astype(np.float32) + region.snaps + float(c[2])
                for j, c in enumerate(owner.cities)
            ],
            dtype=np.float32,
        ).T
        for j, city in enumerate(owner.cities):
            if owner.modern and city[4] in region.point_ids:
                road[region.point_ids.index(city[4]), j] = 0
        access = np.zeros(len(region.nodes))
        for j, city in enumerate(owner.cities):
            times = np.min(road + transfers[:, j].astype(np.float32), axis=1)
            access += city[3] * np.exp(-np.log(2) / 2 * times.astype(np.float64))
        result.append(float(access @ region.population / region.total / owner.norm * 100))
    return result


def candidate(
    tmp_path: Path, owner: Owner, updates: dict[int, dict[int, float]]
) -> tuple[Any, Any]:
    raw = owner.raw.copy()
    trees = {node: SimpleNamespace(overlay=None) for node in (0, 3, 6)}
    for origin, changes in updates.items():
        directory = tmp_path / str(origin)
        directory.mkdir(exist_ok=True)
        nodes = np.array(sorted(changes), dtype=np.int32)
        values = np.array([changes[int(node)] for node in nodes], dtype=np.float64)
        np.save(directory / "nodes.npy", nodes)
        np.save(directory / "distance.npy", values)
        raw[[0, 3, 6].index(origin), nodes] = values
        trees[origin] = SimpleNamespace(overlay=directory)
    return SimpleNamespace(trees=trees), raw


@pytest.mark.parametrize("modern", [True, False])
def test_incremental_region_values_match_full_formula_without_baseline_reads(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, modern: bool
) -> None:
    owner = Owner(modern)
    aggregation = IndexValues(owner, lambda _: None)
    baseline = aggregation.prepare(None, None)
    cache, raw = candidate(tmp_path, owner, {0: {2: 0.25}})
    monkeypatch.setattr(owner, "distances", lambda *args: pytest.fail("Baseline tree reread"))
    actual = aggregation.evaluate(cache, None)
    assert [row.value for row in actual] == pytest.approx(oracle(owner, raw), rel=1e-14)
    assert actual[1] is baseline[1]
    assert aggregation.last_evaluation["touched_regional_origins"] == 1
    assert aggregation.last_evaluation["recomputed_regional_origins"] == 1
    assert aggregation.last_evaluation["transfers_changed"] is False


def test_city_transfer_change_recomputes_all_region_origins(tmp_path: Path) -> None:
    owner = Owner()
    aggregation = IndexValues(owner, lambda _: None)
    aggregation.prepare(None, None)
    cache, raw = candidate(tmp_path, owner, {0: {3: 0.1}, 3: {0: 0.1}})
    actual = aggregation.evaluate(cache, None)
    assert [row.value for row in actual] == pytest.approx(oracle(owner, raw), rel=1e-14)
    assert aggregation.last_evaluation["transfers_changed"] is True
    assert aggregation.last_evaluation["recomputed_regional_origins"] == 4


def test_irrelevant_repaired_node_returns_cached_indices(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner = Owner()
    aggregation = IndexValues(owner, lambda _: None)
    baseline = aggregation.prepare(None, None)
    cache, _ = candidate(tmp_path, owner, {0: {7: 0.1}})
    monkeypatch.setattr(owner, "distances", lambda *args: pytest.fail("Unchanged distance reread"))
    monkeypatch.setattr(
        aggregation, "_access", lambda *args: pytest.fail("Unchanged origin recomputation")
    )
    actual = aggregation.evaluate(cache, None)
    assert all(a is b for a, b in zip(actual, baseline, strict=True))
    assert aggregation.last_evaluation["recomputed_regional_origins"] == 0


def test_legacy_horizon_and_float32_road_rounding_are_preserved(tmp_path: Path) -> None:
    owner = Owner(False)
    owner.raw[0, 2] = 80
    aggregation = IndexValues(owner, lambda _: None)
    baseline = aggregation.prepare(None, None)
    cache, raw = candidate(tmp_path, owner, {0: {2: 75}})
    assert [row.value for row in aggregation.evaluate(cache, None)] == [
        row.value for row in baseline
    ]
    cache, raw = candidate(tmp_path, owner, {0: {2: 70}})
    assert [row.value for row in aggregation.evaluate(cache, None)] == pytest.approx(
        oracle(owner, raw), rel=1e-14
    )


def test_own_market_and_float32_rounding_do_not_create_false_changes(tmp_path: Path) -> None:
    owner = Owner()
    aggregation = IndexValues(owner, lambda _: None)
    baseline = aggregation.prepare(None, None)
    cache, raw = candidate(tmp_path, owner, {3: {4: 0.001}, 0: {2: np.nextafter(2.0, 3.0)}})
    actual = aggregation.evaluate(cache, None)
    assert all(a is b for a, b in zip(actual, baseline, strict=True))
    assert [row.value for row in actual] == pytest.approx(oracle(owner, raw), rel=1e-14)
    assert aggregation.last_evaluation["touched_regional_origins"] == 0


def test_trunk_override_preserves_unchanged_transfers_and_cached_access(tmp_path: Path) -> None:
    owner = Owner(False)
    owner.trunk = [("a", "b", "air", 0.1)]
    aggregation = IndexValues(owner, lambda _: None)
    baseline = aggregation.prepare(None, None)
    cache, raw = candidate(tmp_path, owner, {0: {3: 2.5}})
    actual = aggregation.evaluate(cache, None)
    assert [row.value for row in actual] == pytest.approx(oracle(owner, raw), rel=1e-14)
    assert all(a is b for a, b in zip(actual, baseline, strict=True))
    assert aggregation.last_evaluation["transfers_changed"] is False


def test_municipal_groups_share_regional_markets_normalization_and_scenario_times(tmp_path: Path) -> None:
    owner = Owner()
    owner.population_groups = [
        PopulationGroup("municipality-one", "A", frozenset({"one"}), 40, 1),
        PopulationGroup("municipality-two", "A", frozenset({"two"}), 60, 1),
    ]
    values = IndexValues(owner, lambda _: None)
    before = values.prepare(None, None)
    assert before[0].value == pytest.approx((before[2].value * 40 + before[3].value * 60) / 100)
    changed, raw = candidate(tmp_path, owner, {0: {1: 10.0}, 3: {1: 10.0}, 6: {1: 10.0}})
    after = values.evaluate(changed, None)
    assert after[0].value == pytest.approx(oracle(owner, raw)[0])
    assert after[0].value == pytest.approx((after[2].value * 40 + after[3].value * 60) / 100)
    assert after[2].value < before[2].value
    assert after[3].value == before[3].value
    assert {row.normalization for row in after + before} == {175}
