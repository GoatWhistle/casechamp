from math import exp, log
from typing import TypedDict

import pytest

from app.domain.road_cost import evaluate_road


class ConfirmedArguments(TypedDict):
    length_km: float
    highway: str
    hourly_flow_pcu: float
    flow_verified: bool
    flow_source: str
    flow_period: str


class SharedArguments(ConfirmedArguments):
    lanes_total: int


def test_highway_and_dirt_differ_through_travel_time_without_index_bonus() -> None:
    highway = evaluate_road(length_km=100, highway="motorway", lanes_total=4)
    dirt = evaluate_road(length_km=100, highway="track", surface="dirt", lanes_total=2)
    assert highway.speed_kmh == 90
    assert dirt.speed_kmh == 14
    assert dirt.travel_hours / highway.travel_hours > 6
    assert exp(log(2) / 2 * (dirt.travel_hours - highway.travel_hours)) > 8
    assert highway.flow_basis == dirt.flow_basis == "unknown_free_flow"


def test_missing_flow_widening_reports_capacity_without_inventing_delay() -> None:
    before = evaluate_road(length_km=100, highway="primary", lanes_total=2)
    after = evaluate_road(length_km=100, highway="primary", lanes_total=4)
    assert after.travel_hours == before.travel_hours
    assert after.delay_hours == before.delay_hours == 0
    assert after.capacity_pcu_h == 3600
    assert before.capacity_pcu_h == 1800
    assert "uncalibrated" in after.capacity_basis


def test_fixed_confirmed_flow_widening_reduces_delay() -> None:
    arguments: ConfirmedArguments = {
        "length_km": 100.0,
        "highway": "primary",
        "hourly_flow_pcu": 1800.0,
        "flow_verified": True,
        "flow_source": "validated counter",
        "flow_period": "2025-06-10 08:00/09:00",
    }
    before = evaluate_road(**arguments, lanes_total=2)
    after = evaluate_road(**arguments, lanes_total=4)
    assert before.flow_basis == after.flow_basis == "confirmed"
    assert before.hourly_flow_pcu == after.hourly_flow_pcu
    assert 0 < after.delay_hours < before.delay_hours
    assert before.travel_hours > after.travel_hours


def test_unverified_flow_does_not_slow_road() -> None:
    result = evaluate_road(
        length_km=20,
        highway="primary",
        hourly_flow_pcu=10000,
        flow_source="unmapped historical total",
        flow_period="unknown",
    )
    assert result.flow_basis == "unknown_free_flow"
    assert result.travel_hours == result.free_flow_hours


def test_shared_physical_lane_requires_combined_flow() -> None:
    arguments: SharedArguments = {
        "length_km": 10.0,
        "highway": "road",
        "lanes_total": 1,
        "hourly_flow_pcu": 1800.0,
        "flow_verified": True,
        "flow_source": "combined counter",
        "flow_period": "2025-06-10 08:00/09:00",
    }
    with pytest.raises(ValueError, match="scope"):
        evaluate_road(**arguments)
    result = evaluate_road(**arguments, hourly_flow_scope="bidirectional_total")
    assert result.shared_lane
    assert result.lanes_total == 1
    assert result.effective_lanes == 1
    assert result.capacity_pcu_h == 1800
    assert result.travel_hours == pytest.approx(result.free_flow_hours * 1.15)


def test_unknown_lanes_are_one_per_allowed_direction() -> None:
    two_way = evaluate_road(length_km=10, highway="road")
    reverse = evaluate_road(length_km=10, highway="road", oneway="-1")
    assert (two_way.lanes_total, two_way.lanes_forward, two_way.lanes_backward) == (2, 1, 1)
    assert (reverse.lanes_total, reverse.lanes_forward, reverse.lanes_backward) == (1, 0, 1)
    assert reverse.lane_basis == two_way.lane_basis == "narrow_unknown_lanes_v1"


def test_asymmetric_known_lanes_use_conservative_representative_capacity() -> None:
    result = evaluate_road(
        length_km=10, highway="primary", lanes_total=3, lanes_forward=2, lanes_backward=1
    )
    assert result.effective_lanes == 1
    assert result.capacity_pcu_h == 1800
    assert result.lane_basis == "osm"


def test_posted_speed_is_a_ceiling_and_does_not_raise_existing_priors() -> None:
    capped = evaluate_road(length_km=50, highway="motorway", posted_speed_kmh=50)
    higher_limit = evaluate_road(length_km=50, highway="motorway", posted_speed_kmh=130)
    assert capped.travel_hours == 1
    assert higher_limit.speed_kmh == 90


def test_ferry_retains_source_speed_and_has_no_road_capacity() -> None:
    result = evaluate_road(length_km=12, highway="ferry", surface="dirt", source_speed_kmh=12)
    assert result.travel_hours == 1
    assert result.capacity_pcu_h is None
    assert result.flow_basis == "not_applicable"


@pytest.mark.parametrize(
    "field,value",
    [
        ("length_km", -1),
        ("length_km", float("nan")),
        ("posted_speed_kmh", 0),
        ("posted_speed_kmh", -1),
        ("hourly_flow_pcu", -1),
        ("lanes_total", 0),
        ("lanes_forward", -1),
        ("source_speed_kmh", 0),
    ],
)
def test_invalid_inputs_fail(field: str, value: float) -> None:
    with pytest.raises(ValueError):
        match field:
            case "length_km":
                evaluate_road(length_km=value, highway="primary")
            case "lanes_total":
                evaluate_road(length_km=10, highway="primary", lanes_total=int(value))
            case "lanes_forward":
                evaluate_road(length_km=10, highway="primary", lanes_forward=int(value))
            case "posted_speed_kmh":
                evaluate_road(length_km=10, highway="primary", posted_speed_kmh=value)
            case "source_speed_kmh":
                evaluate_road(length_km=10, highway="primary", source_speed_kmh=value)
            case "hourly_flow_pcu":
                evaluate_road(length_km=10, highway="primary", hourly_flow_pcu=value)
            case _:
                raise AssertionError("Unknown test input")


def test_explicit_design_speed_override_is_final_surface_adjusted_then_legally_capped() -> None:
    designed = evaluate_road(
        length_km=100,
        highway="primary",
        surface="dirt",
        override_speed_kmh=100,
        posted_speed_kmh=100,
    )
    assert designed.speed_kmh == 100
    assert designed.travel_hours == 1
    capped = evaluate_road(
        length_km=100,
        highway="primary",
        surface="dirt",
        override_speed_kmh=100,
        posted_speed_kmh=80,
    )
    assert capped.speed_kmh == 80
    with pytest.raises(ValueError, match="override_speed_kmh"):
        evaluate_road(length_km=100, highway="primary", override_speed_kmh=0)


def test_confirmed_flow_requires_source_and_period() -> None:
    with pytest.raises(ValueError, match="source and observation period"):
        evaluate_road(length_km=10, highway="primary", hourly_flow_pcu=100, flow_verified=True)


def test_zero_length_and_zero_confirmed_flow_remain_zero_cost() -> None:
    result = evaluate_road(
        length_km=0,
        highway="primary",
        hourly_flow_pcu=0,
        flow_verified=True,
        flow_source="counter",
        flow_period="2025-06",
    )
    assert result.travel_hours == result.delay_hours == 0
    assert result.flow_basis == "confirmed"
