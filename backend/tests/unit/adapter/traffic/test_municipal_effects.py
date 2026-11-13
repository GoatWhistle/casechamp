from dataclasses import replace
from pathlib import Path

import numpy as np
import pytest
from synthetic_traffic.incremental import evaluate_incremental, prepare_incremental
from synthetic_traffic.model import Trip
from synthetic_traffic.projects import apply_project
from synthetic_traffic.source import load_network
from tests.unit.adapter.traffic.snapshot_fixture import snapshot

from app.adapter.traffic.municipal_effects import municipal_traffic_metrics
from app.adapter.traffic.municipal_membership import municipal_edge_indices
from app.usecase.municipalities import Municipality


def test_local_time_excludes_outside_edges_and_keeps_lost_local_departures(tmp_path: Path) -> None:
    snapshot(tmp_path)
    graph = load_network(tmp_path)
    municipality = Municipality("M", "R", "M", 6,
        [[[(41.99, 43.99), (42.04, 43.99), (42.04, 44.01), (41.99, 44.01), (41.99, 43.99)]]],
        "source", "2026-11-13", "digest", "polygon", 1)
    trips = [Trip(0, 2, 100)]
    base = prepare_incremental(graph, trips)
    before = municipal_traffic_metrics(municipality, graph, base.assignment, trips)
    assert before.vehicle_hours_on_local_edges == pytest.approx(10 * (1 + .15 * (100 / 1800) ** 4))
    assert before.vehicle_hours_on_local_edges < base.assignment.vehicle_hours_per_hour
    closed = apply_project(graph, {"kind": "closure", "way_ids": [100]})
    after = evaluate_incremental(base, closed)
    effects = municipal_traffic_metrics(municipality, closed, after, trips)
    assert effects.vehicle_hours_on_local_edges == 0
    assert effects.unserved_departures == 100
    assert effects.overloaded_directed_edges == 0


def test_edge_membership_preserves_dateline_crossing(tmp_path: Path) -> None:
    snapshot(tmp_path)
    graph = replace(load_network(tmp_path), lon=np.array([179., -179., 0.]))
    municipality = Municipality("M", "R", "M", 6,
        [[[(178, 43.9), (-178, 43.9), (-178, 44.1), (178, 44.1), (178, 43.9)]]],
        "source", "2026-11-13", "digest", "polygon", 1)
    assert municipal_edge_indices(municipality, graph) == [0, 1]
