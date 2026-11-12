import pytest

from app.domain.errors import InvalidQuery
from app.domain.normative.fire import (
    FireProfile,
    SettlementContext,
    apply_fire_conditions,
    fire_threshold,
)
from app.domain.normative.model import AccessRow


@pytest.mark.parametrize("speed", [0, -1, 201, float("inf"), float("nan")])
def test_invalid_fire_speed_is_rejected(speed: float) -> None:
    with pytest.raises(InvalidQuery):
        FireProfile(speed, "Explicit control assumption")


def test_anonymous_speed_is_not_accepted_as_a_profile() -> None:
    with pytest.raises(InvalidQuery):
        FireProfile(40, " ")


def test_fire_threshold_uses_call_location_category() -> None:
    assert fire_threshold("urban") == 10
    assert fire_threshold("rural") == 20
    assert fire_threshold("urban_okrug") is None
    assert fire_threshold(None) is None
    row = AccessRow("rural-origin", "Origin", 100, 55, 65, "urban-depot", 7, 0, "within")
    result = apply_fire_conditions(
        [row], [SettlementContext(row.id, "rural", "primary", "primary_verified")]
    )[0]
    assert result.threshold_minutes == 20
    assert result.minutes == 7
    assert result.state == "unknown"
    assert result.excess_minutes is None
    assert "fire_readiness_unconfirmed" in result.uncertainty
    assert "territory_conditions_missing" not in result.uncertainty
