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
    positions = np.arange(len(baseline.source))
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
    positions = np.arange(len(network.source))
    adapter = IndexNetwork(edges, np.ones(5, dtype=bool), positions, 5, network, network.free_hours)

    def forbidden(*args: Any, **kwargs: Any) -> Any:
        raise AssertionError("Unchanged national CSR must not be copied")

    monkeypatch.setattr(adapter.base, "copy", forbidden)
    graph, delta = adapter.changed_with_delta(network, network.free_hours)
    assert graph is adapter.base and not len(delta[0])


@pytest.mark.parametrize('directed', [True, False])
@pytest.mark.parametrize('allowed_first', [True, False])
def test_closure_preserves_unowned_parallel_and_reverse_edges(directed: bool, allowed_first: bool) -> None:
    baseline = make_network()
    edges = Snapshot(baseline).arrays('edges')
    edges = {key: np.r_[value, additions] for key, value, additions in (
        ('src', edges['src'], [0, 1]), ('dst', edges['dst'], [1, 0]),
        ('h', edges['h'], [4., 8.]), ('km', edges['km'], [1., 1.]),
        ('way_idx', edges['way_idx'], [9, 10]),
    )}
    allowed = np.ones(7, dtype=bool)
    allowed[0] = allowed_first
    adapter = IndexNetwork(edges, allowed, np.arange(5), 5, baseline, baseline.free_hours, directed)
    closed = apply_project(baseline, {'kind': 'closure', 'way_ids': [100, 101]})
    graph, delta = adapter.changed_with_delta(closed, closed.free_hours)
    assert graph[0, 1] == 4.
    assert graph[1, 0] == (8. if directed else 4.)
    assert adapter.base[1, 0] == 1.
    expected = cast(Callable[[Any, Any], tuple[Any, Any, Any, Any]], changes)(adapter.base, graph)
    for actual, wanted in zip(delta, expected, strict=True):
        np.testing.assert_array_equal(actual, wanted)


@pytest.mark.parametrize('directed', [True, False])
def test_numeric_scenario_graph_matches_independent_parallel_minimum(directed: bool) -> None:
    random = np.random.default_rng(821)
    baseline = make_network()
    edges = Snapshot(baseline).arrays('edges')
    for _ in range(20):
        allowed = random.random(5) > .2
        adapter = IndexNetwork(edges, allowed, np.arange(5), 5, baseline, baseline.free_hours, directed)
        selected = np.flatnonzero(random.random(5) > .4)
        if not len(selected):
            selected = np.array([0])
        changed = replace(baseline, **{name: getattr(baseline, name)[selected] for name in
                          ('source', 'target', 'free_hours', 'capacity', 'length_km', 'way_id', 'shared')})
        hours = random.uniform(.1, 10, len(selected))
        graph, _ = adapter.changed_with_delta(changed, hours)
        oracle = np.full((5, 5), np.inf)
        for edge, hour in zip(selected, hours, strict=True):
            if not allowed[edge]:
                continue
            a, b = int(baseline.source[edge]), int(baseline.target[edge])
            oracle[a, b] = min(oracle[a, b], hour)
            if not directed:
                oracle[b, a] = min(oracle[b, a], hour)
        actual = graph.toarray()
        actual[actual == 0] = np.inf
        np.testing.assert_array_equal(actual, oracle)
