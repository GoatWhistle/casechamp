import re
from dataclasses import dataclass, replace
from typing import Literal

from app.domain.normative.model import AccessRow, Uncertainty

MunicipalityType = Literal["urban_okrug", "municipal_okrug"]
ENCODED_PARENT_STATUS = "encoded_parent_2024_assignment_unconfirmed"


@dataclass(frozen=True, slots=True)
class TerritoryContext:
    point_id: str
    municipality_type: MunicipalityType
    source_url: str
    verification_status: str
    municipality_code: str | None = None
    structure_source_url: str | None = None

    def __post_init__(self) -> None:
        if self.verification_status == ENCODED_PARENT_STATUS and (
            re.fullmatch(r"[0-9]{11}", self.point_id) is None
            or self.municipality_code != self.point_id[:8]
            or not self.structure_source_url
        ):
            raise ValueError("Encoded territorial evidence requires an exact parent and source")


def library_threshold(municipality_type: MunicipalityType | None) -> float | None:
    if municipality_type == "urban_okrug":
        return 40
    if municipality_type == "municipal_okrug":
        return 60
    return None


def apply_library_conditions(
    rows: list[AccessRow], territories: list[TerritoryContext]
) -> list[AccessRow]:
    if len({item.point_id for item in territories}) != len(territories):
        raise ValueError("Conflicting territorial contexts")
    contexts = {item.point_id: item for item in territories}
    result = []
    for row in rows:
        context = contexts.get(row.id)
        threshold = library_threshold(context.municipality_type if context else None)
        reasons: list[Uncertainty] = [
            *row.uncertainty,
            "transport_mode_unconfirmed",
            "facility_profile_unconfirmed",
            "facility_entrances_unverified",
        ]
        if (
            context is None
            or threshold is None
            or context.verification_status != "primary_verified"
        ):
            reasons.append("territory_conditions_missing")
        result.append(
            replace(
                row,
                state="unknown",
                excess_minutes=None,
                threshold_minutes=threshold,
                territory_type=context.municipality_type if context else None,
                territory_source_url=context.source_url if context else None,
                territory_verification_status=context.verification_status if context else None,
                municipality_code=context.municipality_code if context else None,
                territory_structure_source_url=context.structure_source_url if context else None,
                uncertainty=tuple(dict.fromkeys(reasons)),
            )
        )
    return result
