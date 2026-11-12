from collections.abc import Callable
from dataclasses import replace
from typing import Any, cast

import numpy as np
import pytest
from synthetic_traffic.index_path_repair import changes
from synthetic_traffic.projects import apply_project
from tests.unit.adapter.traffic.test_index_delta import Snapshot, make_network

from app.adapter.traffic.index_network import IndexNetwork


@pytest.mark.parametrize(
    "kind", ["identity", "increase_parallel", "decrease", "closure", "connections"]
)
def test_explicit_delta_matches_complete_csr_difference(kind: str) -> None:
    baseline = make_network()
    edges = Snapshot(baseline).arrays("edges")
    positions = {
        (int(a), int(b), int(w)): i
        for i, (a, b, w) in enumerate(
            zip(baseline.source, baseline.target, baseline.way_id, strict=True)
        )
    }
    adapter = IndexNetwork(
        edges,
        np.ones(len(baseline.source), dtype=bool),
        positions,
        5,
        baseline,
        baseline.free_hours,
    )
    network = baseline
    hours = baseline.free_hours.copy()
    if kind == "increase_parallel":
        hours[0] += 2
    elif kind == "decrease":
        hours[0] = 0.25
    elif kind == "closure":
        network = apply_project(baseline, {"kind": "closure", "way_ids": [100, 101]})
        hours = hours[2:]
    elif kind == "connections":
        network = replace(
            baseline,
            source=np.r_[baseline.source, 0, 2],
            target=np.r_[baseline.target, 4, 4],
            way_id=np.r_[baseline.way_id, -1, -2],
            free_hours=np.r_[baseline.free_hours, 0.5, 0.75],
            capacity=np.r_[baseline.capacity, 100.0, 100.0],
            length_km=np.r_[baseline.length_km, 1.0, 1.0],
            shared=np.r_[baseline.shared, -1, -1],
        )
        hours = np.r_[hours, 0.5, 0.75]
    graph, delta = adapter.changed_with_delta(network, hours)
    expected = cast(Callable[[Any, Any], tuple[Any, Any, Any, Any]], changes)(adapter.base, graph)
    actual_order = np.lexsort((delta[1], delta[0]))
    for actual, wanted in zip(delta, expected, strict=True):
        np.testing.assert_array_equal(actual[actual_order], wanted)
    if kind in {"identity", "increase_parallel"}:
        assert graph is adapter.base
        assert not len(delta[0])


def test_identity_preserves_baseline_without_copy(monkeypatch: pytest.MonkeyPatch) -> None:
    network = make_network()
    edges = Snapshot(network).arrays("edges")
    positions = {
        (int(a), int(b), int(w)): i
        for i, (a, b, w) in enumerate(
            zip(network.source, network.target, network.way_id, strict=True)
        )
    }
    adapter = IndexNetwork(edges, np.ones(5, dtype=bool), positions, 5, network, network.free_hours)

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("Unchanged national CSR must not be copied")

    monkeypatch.setattr(adapter.base, "copy", forbidden)
    graph, delta = adapter.changed_with_delta(network, network.free_hours)
    assert graph is adapter.base and not len(delta[0])
