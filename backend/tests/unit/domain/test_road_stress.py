from math import inf

import pytest

from app.domain.road_stress import compare_market_times


def test_long_route_is_reachable() -> None:
    assert compare_market_times([80], [90], ["market"], "")[0:3] == (0, False, 600)


def test_own_market_does_not_hide_isolation() -> None:
    assert compare_market_times([0, 2], [0, inf], ["home", "other"], "home")[:2] == (1, True)


def test_preexisting_disconnection_is_not_new_isolation() -> None:
    assert compare_market_times([inf], [inf], ["market"], "")[:3] == (0, False, 0)


def test_closing_a_road_cannot_improve_time() -> None:
    with pytest.raises(ValueError):
        compare_market_times([2], [1], ["market"], "")


def test_partial_loss_keeps_external_access() -> None:
    assert compare_market_times([1, 2], [inf, 3], ["a", "b"], "")[:3] == (1, False, 60)


def test_untouched_markets_are_not_affected() -> None:
    assert compare_market_times([1, 2], [1, 2], ["a", "b"], "") == (0, False, 0, "")
