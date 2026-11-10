import numpy as np
import pytest

from app.domain.accessibility import access_by_half_life, departure_cost


def test_unknown_frequency_is_not_a_weekly_departure() -> None:
    unknown = departure_cost(2, "air", None)
    assumed = departure_cost(2, "air", 1, assumed=True)
    assert unknown == assumed
    assert unknown.planned_hours == 4.5
    assert unknown.frequency_per_week is None
    assert unknown.expected_hours is None


def test_observed_frequency_changes_waiting_but_not_planned_trip() -> None:
    daily = departure_cost(2, "air", 7)
    weekly = departure_cost(2, "air", 1)
    assert daily.planned_hours == weekly.planned_hours == 4.5
    assert daily.expected_hours == 16.5
    assert weekly.expected_hours == 88.5


def test_unreachable_market_contributes_zero_and_two_hours_halves_access() -> None:
    times = np.array([[0.0, np.inf], [2.0, np.inf], [4.0, np.inf]])
    np.testing.assert_allclose(
        access_by_half_life(times, np.array([100.0, 900.0]), 2), [100, 50, 25]
    )


@pytest.mark.parametrize("frequency", [0, -1, float("nan"), float("inf")])
def test_invalid_frequency_is_rejected(frequency: float) -> None:
    with pytest.raises(ValueError):
        departure_cost(1, "rail", frequency)


def test_ferry_and_river_keep_boarding_cost_without_inventing_frequency() -> None:
    for mode in ("ferry", "river"):
        cost = departure_cost(1, mode, None)
        assert cost.planned_hours == 1.5
        assert cost.expected_hours is None
