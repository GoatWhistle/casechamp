from dataclasses import dataclass, replace
from math import isfinite
from typing import Literal

from app.domain.errors import InvalidQuery
from app.domain.normative.model import AccessRow, Uncertainty


@dataclass(frozen=True, slots=True)
class FireProfile:
    speed_kmh: float
    assumption: str

    def __post_init__(self) -> None:
        if (
            isinstance(self.speed_kmh, bool)
            or not isfinite(self.speed_kmh)
            or not 0 < self.speed_kmh <= 200
        ):
            raise InvalidQuery("Fire scenario speed must be finite and between 0 and 200 km/h")
        if not 8 <= len(self.assumption.strip()) <= 500:
            raise InvalidQuery("Describe the fire travel speed assumption in 8 to 500 characters")


@dataclass(frozen=True, slots=True)
class SettlementContext:
    point_id: str
    settlement_type: Literal["urban", "rural"]
    source_url: str
    verification_status: str


def fire_threshold(settlement_type: str | None) -> float | None:
    return {"urban": 10.0, "rural": 20.0}.get(settlement_type or "")


def apply_fire_conditions(
    rows: list[AccessRow], settlements: list[SettlementContext]
) -> list[AccessRow]:
    if len({item.point_id for item in settlements}) != len(settlements):
        raise ValueError("Conflicting settlement contexts")
    contexts = {item.point_id: item for item in settlements}
    result = []
    for row in rows:
        context = contexts.get(row.id)
        threshold = fire_threshold(context.settlement_type if context else None)
        reasons: list[Uncertainty] = [
            *row.uncertainty,
            "fire_speed_assumed",
            "fire_vehicle_access_unconfirmed",
            "fire_readiness_unconfirmed",
            "facility_entrances_unverified",
        ]
        if (
            context is None
            or context.verification_status != "primary_verified"
            or threshold is None
        ):
            reasons.append("territory_conditions_missing")
        result.append(
            replace(
                row,
                state="unknown",
                excess_minutes=None,
                threshold_minutes=threshold,
                territory_type=context.settlement_type if context else None,
                territory_source_url=context.source_url if context else None,
                uncertainty=tuple(dict.fromkeys(reasons)),
            )
        )
    return result
