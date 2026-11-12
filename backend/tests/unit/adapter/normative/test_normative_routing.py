from dataclasses import replace
from types import SimpleNamespace
from typing import cast

import numpy as np
import pytest

from app.adapter.normative.routing import GraphNormativeRouting
from app.adapter.road_graph.delta_base import DeltaBase
from app.adapter.road_graph.routing import minimum_csr
from app.domain.errors import InvalidQuery
from app.domain.normative.model import Facility, Origin


def setup_routing() -> tuple[GraphNormativeRouting, list[Origin], Facility]:
    edges = {
        "src": np.array([0, 1, 0]),
        "dst": np.array([1, 2, 1]),
        "h": np.array([0.5, 0.5, 1.0]),
        "way_idx": np.array([0, 1, 2]),
    }
    data = SimpleNamespace(
        revision="test",
        edges=edges,
        nodes={"lat": np.array([55.0, 55.1, 55.2]), "lon": np.array([65.0, 65.0, 65.0])},
        allowed_edges=lambda _: np.array([True, True, True]),
        read=lambda _, params: [(10, 0)] if params["ids"] == [10] else [],
    )
    base = SimpleNamespace(
        data=data,
        graph=minimum_csr(edges["src"], edges["dst"], edges["h"], 3),
        prepare=lambda: None,
    )
    origins = [Origin("a", "A", 10, 2, 0, 55.2, 65), Origin("b", "B", 20, None, None, 55.5, 65)]
    facility = Facility(
        "f",
        "mfc",
        "Office",
        "Address",
        "https://example.org",
        "2026-11-11",
        55,
        65,
        "https://example.org",
        "geocoded_building",
    )
    return GraphNormativeRouting(cast(DeltaBase, base)), origins, facility


def test_missing_facility_coordinates_do_not_mean_proven_inaccessibility() -> None:
    routing, origins, facility = setup_routing()
    result = routing.evaluate(origins, [facility], 30, [])
    assert result[0].minutes == pytest.approx(60)
    assert result[0].state == "unknown"
    assert result[1].state == "unknown"


def test_closure_preserves_parallel_alternative_and_changes_time() -> None:
    routing, origins, facility = setup_routing()
    before = routing.evaluate(origins, [facility], 60, [])
    after = routing.evaluate(origins, [facility], 60, [10])
    assert before[0].state == "within"
    assert after[0].minutes == pytest.approx(90)
    assert after[0].state == "unknown"
    assert before[0].minutes == pytest.approx(60)


def test_unknown_road_is_rejected_instead_of_silently_ignored() -> None:
    routing, origins, facility = setup_routing()
    with pytest.raises(InvalidQuery):
        routing.evaluate(origins, [facility], 60, [999])


def test_road_trace_replays_the_parallel_closure_cost() -> None:
    routing, origins, facility = setup_routing()
    row = routing.evaluate(origins, [facility], 60, [10])[0]
    route = routing.trace(origins[0], facility, [10], "test")
    assert route.minutes == pytest.approx(row.minutes)
    assert route.network_coordinates == [(65, 55.2), (65, 55.1), (65, 55)]


def test_many_regional_facilities_use_the_same_minimum_and_replayable_target() -> None:
    routing, origins, facility = setup_routing()
    facilities = [replace(facility, id=f"facility-{index}") for index in range(35)]
    rows = routing.evaluate(origins, facilities, 0, [])
    assert rows[0].minutes == pytest.approx(60)
    target = next(row for row in facilities if row.id == rows[0].facility_id)
    assert routing.trace(origins[0], target, [], "test").minutes == pytest.approx(rows[0].minutes)
    assert rows[1].minutes is None
