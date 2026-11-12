import pytest

from app.domain.normative.model import AccessRow, AccessState, coverage


def row(state: AccessState, population: int | None) -> AccessRow:
    return AccessRow("a", "A", population, None, None, None, None, None, state)


def test_unknown_people_define_bounds_without_disappearing_from_denominator() -> None:
    result = coverage([row("within", 60), row("unknown", 30), row("exceeded", 10)])
    assert result.population == 100
    assert result.lower_percent == 60
    assert result.upper_percent == 90


def test_missing_population_prevents_percentage_claims() -> None:
    result = coverage([row("within", 100), row("unknown", None)])
    assert result.lower_percent is None
    assert result.upper_percent is None
    assert result.unknown_population_points == 1


def test_zero_population_has_no_defined_percentage() -> None:
    assert coverage([row("within", 0)]).lower_percent is None


def test_unreachable_is_not_zero_minutes_or_unknown_when_inventory_complete() -> None:
    result = coverage([row("within", 70), row("unreachable", 30)])
    assert result.lower_percent == result.upper_percent == 70
    assert result.unreachable == 30


def test_negative_population_is_rejected() -> None:
    with pytest.raises(ValueError):
        coverage([row("within", -1)])
