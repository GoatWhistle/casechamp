import pytest

from app.domain.road_cost import evaluate_road


@pytest.mark.parametrize(
    "mode,forward,backward",
    [
        ("forward", 3, 0),
        ("reverse", 0, 3),
        ("yes", 3, 0),
        ("-1", 0, 3),
    ],
)
def test_canonical_oneway_and_prohibited_zero(mode: str, forward: int, backward: int) -> None:
    result = evaluate_road(
        length_km=10,
        highway="primary",
        oneway=mode,
        lanes_total=3,
        lanes_forward=forward,
        lanes_backward=backward,
    )
    assert (result.lanes_forward, result.lanes_backward) == (forward, backward)
    assert result.effective_lanes == 3
    assert result.capacity_pcu_h == 5400


def test_invalid_source_metadata_retains_raw_values_without_guessing_capacity() -> None:
    result = evaluate_road(
        length_km=10,
        highway="primary",
        lanes_total=3,
        lanes_forward=4,
        lanes_backward=1,
        lane_data_usable=False,
    )
    assert result.lane_basis == "unresolved"
    assert result.lanes_total == 3
    assert result.lanes_forward == 4
    assert result.capacity_pcu_h is None
    assert result.travel_hours == result.free_flow_hours
    with pytest.raises(ValueError, match="resolved lane metadata"):
        evaluate_road(
            length_km=10,
            highway="primary",
            lane_data_usable=False,
            hourly_flow_pcu=100,
            flow_verified=True,
            flow_source="counter",
            flow_period="2025",
        )


@pytest.mark.parametrize("mode", ["alternating", "reversible"])
def test_conditional_oneway_has_no_invented_capacity(mode: str) -> None:
    result = evaluate_road(length_km=10, highway="road", oneway=mode, lanes_total=1)
    assert result.capacity_pcu_h is None
    assert result.lane_basis == "unresolved"
    assert result.delay_hours == 0


def test_zero_lanes_on_two_way_side_are_not_reinterpreted_as_missing() -> None:
    with pytest.raises(ValueError, match="zero lanes"):
        evaluate_road(
            length_km=10,
            highway="primary",
            oneway="bidirectional",
            lanes_total=3,
            lanes_forward=3,
            lanes_backward=0,
        )
