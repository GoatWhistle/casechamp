from dataclasses import replace

from app.domain.normative.model import AccessRow, Criterion

ADULT_CARDIOLOGY = frozenset({"emergency_cardiology", "urgent_cardiology"})


def apply_population_scope(criterion: Criterion, rows: list[AccessRow]) -> list[AccessRow]:
    if criterion.service not in ADULT_CARDIOLOGY:
        return rows
    return [
        replace(
            row,
            population=None,
            state="unknown",
            excess_minutes=None,
            uncertainty=(
                *row.uncertainty,
                "population_group_missing",
                "medical_catchment_unconfirmed",
                "facility_entrances_unverified",
            ),
        )
        for row in rows
    ]
