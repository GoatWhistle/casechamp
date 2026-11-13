from dataclasses import replace
from pathlib import Path
from time import monotonic
from typing import Any, Literal, cast

import numpy as np
import pytest
import synthetic_traffic.incremental_paths as paths
from synthetic_traffic.model import Network

from app.adapter.road_graph.data import GraphData
from app.adapter.road_graph.routing import GraphRouting
from app.adapter.traffic.index_delta import IndexDelta
from app.usecase.graph_snapshot import GraphParameters, GraphQuery


class Snapshot:
    revision = "index-delta-fixture"

    def __init__(
        self, network: Network, own_market: bool = False, zero_population: bool = False
    ) -> None:
        self.network = network
        self.own_market = own_market
        self.zero_population = zero_population

    def arrays(self, name: Literal["edges", "nodes", "ranks", "seasons"]) -> dict[str, Any]:
        network = self.network
        if name == "edges":
            return {
                "src": network.source,
                "dst": network.target,
                "h": network.free_hours,
                "km": network.length_km,
                "way_idx": np.arange(len(network.source)),
            }
        if name == "nodes":
            return {"lat": network.lat, "lon": network.lon}
        if name == "seasons":
            return {"season": np.zeros(len(network.source), dtype=np.uint8)}
        return {"rank": np.full(len(network.source), 2)}

    def read(
        self, query: GraphQuery, parameters: GraphParameters | None = None
    ) -> list[tuple[Any, ...]]:
        if query == "way_indices":
            assert parameters is not None
            return [
                (int(w), i)
                for i, w in enumerate(self.network.way_id)
                if int(w) in cast(list[int], parameters["ids"])
            ]
        rows: dict[str, list[tuple[Any, ...]]] = {
            "model_version": [("hansen-frequency-v2",)],
            "road_cost_model": [],
            "points": [("origin", 0, 7.5), ("other", 2, 3.0), ("off", -1, 0.0)],
            "origins": [
                ("origin", 0 if self.zero_population else 40),
                ("other", 0 if self.zero_population else 20),
                ("off", 0 if self.zero_population else 40),
            ],
            "cities": [
                ("near", 0, 0.1, 30.0, "origin" if self.own_market else "near-id"),
                ("far", 4, 0.2, 100.0, "far-id"),
            ],
            "normalization": [(175.0,)],
            "trunk": [],
            "manual": [],
            "manual_v2": [],
        }
        return rows[query]


def make_network() -> Network:
    return Network(
        source=np.array([0, 1, 1, 0, 3]),
        target=np.array([1, 0, 2, 2, 4]),
        free_hours=np.array([3.0, 1.0, 2.0, 7.0, 1.0]),
        capacity=np.full(5, 100.0),
        length_km=np.ones(5),
        way_id=np.arange(100, 105),
        raw_nodes=np.arange(5),
        lat=np.zeros(5),
        lon=np.arange(5, dtype=float),
        shared=np.full(5, -1),
    )


def full_value(tmp_path: Path, network: Network, own_market: bool = False) -> float:
    data = GraphData(tmp_path, Snapshot(network, own_market))
    return GraphRouting(data).calculate_details("region", "road", [], lambda _: None)[0][0]


@pytest.mark.parametrize("change", ["identity", "direction_min", "closure", "multi_connection"])
def test_delta_matches_full_road_formula(tmp_path: Path, change: str) -> None:
    network = make_network()
    delta = IndexDelta(
        GraphData(tmp_path, Snapshot(network)),
        network,
        network.free_hours,
        ["region"],
        lambda: None,
    )
    assert delta.baseline[0].value == pytest.approx(full_value(tmp_path, network), rel=2e-7)
    assert (
        delta.baseline[0].population,
        delta.baseline[0].settlements,
        delta.baseline[0].normalization,
    ) == (100, 3, 175.0)
    if change == "direction_min":
        hours = network.free_hours.copy()
        hours[0] = 0.3
        network = replace(network, free_hours=hours)
    elif change == "closure":
        selected = np.array([0, 2, 3, 4])
        network = replace(
            network,
            **{
                name: getattr(network, name)[selected]
                for name in [
                    "source",
                    "target",
                    "free_hours",
                    "capacity",
                    "length_km",
                    "way_id",
                    "shared",
                ]
            },
        )
    elif change == "multi_connection":
        network = replace(
            network,
            **{
                name: np.r_[getattr(network, name), values]
                for name, values in {
                    "source": [2, 1],
                    "target": [3, 4],
                    "free_hours": [0.3, 2.0],
                    "capacity": [100.0, 100.0],
                    "length_km": [1.0, 1.0],
                    "way_id": [-1, -2],
                    "shared": [-1, -1],
                }.items()
            },
        )
    actual = delta.evaluate(network, network.free_hours, monotonic() + 5)
    assert actual[0].value == pytest.approx(full_value(tmp_path, network), rel=2e-7)


def test_self_market_snap_transfer_matches_full_formula(tmp_path: Path) -> None:
    network = make_network()
    network = replace(
        network,
        source=np.r_[network.source, 2],
        target=np.r_[network.target, 3],
        free_hours=np.r_[network.free_hours, 1.0],
        capacity=np.r_[network.capacity, 100.0],
        length_km=np.r_[network.length_km, 1.0],
        way_id=np.r_[network.way_id, 105],
        shared=np.r_[network.shared, -1],
    )
    delta = IndexDelta(
        GraphData(tmp_path, Snapshot(network, own_market=True)),
        network,
        network.free_hours,
        ["region"],
        lambda: None,
    )
    assert delta.baseline[0].value == pytest.approx(
        full_value(tmp_path, network, own_market=True), rel=2e-7
    )


def test_zero_population_rejects_like_full_formula(tmp_path: Path) -> None:
    network = make_network()
    with pytest.raises(ValueError, match="Population"):
        IndexDelta(
            GraphData(tmp_path, Snapshot(network, zero_population=True)),
            network,
            network.free_hours,
            ["region"],
            lambda: None,
        )


@pytest.mark.parametrize("known_point", [True, False])
def test_virtual_market_preserves_missing_point_semantics(
    tmp_path: Path, known_point: bool
) -> None:
    class VirtualSnapshot(Snapshot):
        def read(
            self, query: GraphQuery, parameters: GraphParameters | None = None
        ) -> list[tuple[Any, ...]]:
            rows = super().read(query, parameters)
            if query == "points" and known_point:
                return [*rows, ("virtual", -1, 9.0)]
            if query == "origins":
                return [*rows, ("virtual", 50)]
            if query == "cities":
                return [*rows, ("virtual-market", 5, 0.2, 120.0, "virtual")]
            return rows

    network = make_network()
    data = GraphData(tmp_path, VirtualSnapshot(network))
    expected = GraphRouting(data).calculate_details("region", "road", [], lambda _: None)[0][0]
    delta = IndexDelta(data, network, network.free_hours, ["region"], lambda: None)
    assert delta.baseline[0].value == pytest.approx(expected, rel=2e-7)


def test_candidate_uses_cached_trees_without_full_dijkstra(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    network = make_network()
    delta = IndexDelta(
        GraphData(tmp_path, Snapshot(network)),
        network,
        network.free_hours,
        ["region"],
        lambda: None,
    )
    hours = network.free_hours.copy()
    hours[0] = 0.3
    changed = replace(network, free_hours=hours)
    expected = full_value(tmp_path, changed)

    def reject(*args: Any, **kwargs: Any) -> None:
        raise AssertionError("Candidate must not run full shortest-path recomputation")

    monkeypatch.setattr(paths, "dijkstra", reject)
    assert delta.evaluate(changed, hours, monotonic() + 5)[0].value == pytest.approx(
        expected, rel=2e-7
    )


class LegacySnapshot(Snapshot):
    def read(
        self, query: GraphQuery, parameters: GraphParameters | None = None
    ) -> list[tuple[Any, ...]]:
        if query == "model_version":
            return [("road-capacity-v1",)]
        if query == "trunk":
            return [("near", "far", "rail", 1.0)]
        return super().read(query, parameters)


def test_current_capacity_snapshot_preserves_legacy_horizon_and_transfers(tmp_path: Path) -> None:
    network = make_network()
    network.free_hours[2] = 80
    data = GraphData(tmp_path, LegacySnapshot(network, own_market=True))
    delta = IndexDelta(data, network, network.free_hours, ["region"], lambda: None)
    expected = GraphRouting(data).calculate_details("region", "road", [], lambda _: None)[0][0]
    assert delta.baseline[0].value == pytest.approx(expected, rel=2e-7)


def test_unchanged_float64_assignment_does_not_create_float32_graph_diffs(tmp_path: Path) -> None:
    class FloatSnapshot(Snapshot):
        def arrays(self, name: Literal["edges", "nodes", "ranks", "seasons"]) -> dict[str, Any]:
            values = super().arrays(name)
            if name == "edges":
                values["h"] = values["h"].astype(np.float32)
            return values

    network = make_network()
    network.free_hours[:] = 0.123456789
    delta = IndexDelta(
        GraphData(tmp_path, FloatSnapshot(network)),
        network,
        network.free_hours,
        ["region"],
        lambda: None,
    )
    changed = delta.network.changed(network, network.free_hours)
    assert np.array_equal(changed.data, delta.network.base.data)


def test_directed_city_access_uses_routes_to_markets_and_preserves_one_way_closure(tmp_path: Path) -> None:
    original = make_network()
    network = replace(original, **{
        key: np.r_[getattr(original, key), value]
        for key, value in {
            "source": 2, "target": 3, "free_hours": 1., "capacity": 100.,
            "length_km": 1., "way_id": 105, "shared": -1,
        }.items()
    })
    delta = IndexDelta(GraphData(tmp_path, Snapshot(network)), network, network.free_hours,
                       ["region"], lambda: None, directed=True)
    decay = np.log(2) / 2
    expected = (40 * (30 * np.exp(-decay * .6) + 100 * np.exp(-decay * 7.7))
                + 20 * 100 * np.exp(-decay * 2.4)) / 175
    assert delta.baseline[0].value == pytest.approx(expected, rel=2e-7)
    assert delta.network.base[4, 3] == 0
    selected = np.arange(1, 6)
    closed = replace(network, **{
        key: getattr(network, key)[selected]
        for key in ("source", "target", "free_hours", "capacity", "length_km", "way_id", "shared")
    })
    result = delta.evaluate(closed, closed.free_hours)
    expected_after = (40 * (30 * np.exp(-decay * .6) + 100 * np.exp(-decay * 9.7))
                      + 20 * 100 * np.exp(-decay * 2.4)) / 175
    assert result[0].value == pytest.approx(expected_after, rel=2e-7)
    assert result[0].value < delta.baseline[0].value


def test_live_index_scenario_requires_precomputed_market_trees(tmp_path: Path) -> None:
    network = make_network()
    data = GraphData(tmp_path, Snapshot(network))
    with pytest.raises(FileNotFoundError, match="offline preparation"):
        IndexDelta(data, network, network.free_hours, ["region"], lambda: None,
                   directed=True, require_cached=True)
    prepared = IndexDelta(data, network, network.free_hours, ["region"], lambda: None, directed=True)
    restored = IndexDelta(data, network, network.free_hours, ["region"], lambda: None,
                          directed=True, require_cached=True)
    assert restored.baseline == prepared.baseline


def test_scenario_uses_published_normalization_instead_of_reaggregating(tmp_path: Path) -> None:
    network = make_network()
    data = GraphData(tmp_path, Snapshot(network))
    baseline = IndexDelta(data, network, network.free_hours, ["region"], lambda: None,
                          directed=True, normalization=200)
    assert baseline.baseline[0].normalization == 200
    after = baseline.evaluate(network, network.free_hours)
    assert after == baseline.baseline
    with pytest.raises(ValueError, match="normalization"):
        IndexDelta(data, network, network.free_hours, ["region"], lambda: None,
                   directed=True, normalization=float('nan'))
