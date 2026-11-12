from dataclasses import replace

import numpy as np
import pytest
from synthetic_traffic.assignment import assign
from synthetic_traffic.model import Network, Trip
from synthetic_traffic.objectives import build_objective


def scene():
    network = Network(
        source=np.array([0, 1, 3]),
        target=np.array([1, 2, 4]),
        free_hours=np.ones(3),
        capacity=np.full(3, 10.0),
        length_km=np.ones(3),
        way_id=np.arange(3),
        raw_nodes=np.arange(5),
        lat=np.array([0.0, 0.0, 0.0, 3.0, 3.0]),
        lon=np.array([-2.0, 0.0, 2.0, -2.0, 2.0]),
        shared=np.full(3, -1),
    )
    trips = [Trip(0, 2, 5.0), Trip(0, 1, 3.0), Trip(3, 4, 5.0)]
    return network, trips, assign(network, trips)


def test_congestion_uses_focused_delay_and_ignores_outside_delays():
    network, trips, baseline = scene()
    scorer = build_objective(
        "congestion", network, baseline, trips, [-0.2, -0.2, 0.2, 0.2]
    )
    expected = float((baseline.flow[:2] * (baseline.hours[:2] - 1)).sum())
    assert scorer(network, baseline) == pytest.approx(-expected)
    hours = baseline.hours.copy()
    hours[2] += 100
    assert scorer(network, replace(baseline, hours=hours)) == pytest.approx(-expected)
    improved = replace(baseline, hours=network.free_hours.copy())
    assert scorer(network, improved) == 0
    assert scorer.metrics(network, baseline)[
        "focused_delay_vehicle_hours_per_hour"
    ] == pytest.approx(expected)


def test_transit_automatically_fixes_external_od_crossing_focus():
    network, trips, baseline = scene()
    scorer = build_objective(
        "transit", network, baseline, trips, [-0.2, -0.2, 0.2, 0.2]
    )
    np.testing.assert_array_equal(scorer.selected, [True, False, False])
    assert scorer(network, baseline) == pytest.approx(-baseline.od_hours[0])
    hours = list(baseline.od_hours)
    hours[0], hours[1] = 0.5, 999.0
    assert scorer(network, replace(baseline, od_hours=hours)) == -0.5
    assert scorer.metrics(network, baseline)["selected_vehicles_per_hour"] == 5


def test_transit_detects_road_crossing_without_an_inside_node():
    network, trips, baseline = scene()
    scorer = build_objective("transit", network, baseline, trips, [-0.2, 2.8, 0.2, 3.2])
    np.testing.assert_array_equal(scorer.selected, [False, False, True])


def test_explicit_transit_mask_needs_no_focus_and_uses_fixed_weighting():
    network, trips, baseline = scene()
    scorer = build_objective(
        "transit", network, baseline, trips, transit_mask=[True, True, False]
    )
    expected = (baseline.od_hours[0] * 5 + baseline.od_hours[1] * 3) / 8
    assert scorer(network, baseline) == pytest.approx(-expected)
    assert scorer.metrics(network, baseline)["transit_mean_minutes"] == pytest.approx(
        expected * 60
    )


@pytest.mark.parametrize("objective", ["transit", "congestion"])
def test_dropped_or_unknown_demand_cannot_improve_score(objective):
    network, trips, baseline = scene()
    scorer = build_objective(
        objective, network, baseline, trips, [-0.2, -0.2, 0.2, 0.2]
    )
    for changed in (
        replace(baseline, unserved_vehicles_per_hour=1),
        replace(baseline, unserved_vehicles_per_hour=float("nan")),
        replace(baseline, od_hours=[None, *baseline.od_hours[1:]]),
        replace(baseline, converged=False),
    ):
        assert scorer(network, changed) == -float("inf")
        assert scorer.metrics(network, changed)["eligible"] is False


def test_missing_focus_or_invalid_subset_fails_clearly():
    network, trips, baseline = scene()
    with pytest.raises(ValueError, match="requires focus"):
        build_objective("transit", network, baseline, trips)
    with pytest.raises(ValueError, match="No reachable"):
        build_objective("transit", network, baseline, trips, [10, 10, 11, 11])
    with pytest.raises(ValueError, match="boolean mask"):
        build_objective("transit", network, baseline, trips, transit_mask=[1, 0, 0])
    with pytest.raises(ValueError, match="connectivity"):
        build_objective("connectivity", network, baseline, trips)
