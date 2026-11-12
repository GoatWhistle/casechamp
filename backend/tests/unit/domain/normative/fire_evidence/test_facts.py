from collections.abc import Callable
from dataclasses import asdict
from typing import cast

import pytest
from tests.unit.domain.normative.fire_evidence.factories import facts

from app.domain.errors import InvalidQuery
from app.domain.normative.fire import FireProfile
from app.domain.normative.fire_evidence.facts import FireFacts


@pytest.mark.parametrize(
    "changes",
    [
        {"speed_kmh": True},
        {"speed_kmh": float("nan")},
        {"speed_kmh": 201},
        {"speed_source_url": None},
        {"profile_assumption": None},
        {"profile_assumption": "short"},
        {"vehicle_access_verified": "false"},
        {"operational_readiness_verified": 1},
        {"directionality_verified": None},
        {"transport_mode": "car"},
        {"settlement_type": None},
        {"settlement_type": "suburb"},
        {"population_scope": None},
    {"population_partition_verified": False},
        {"population_scope": "settlement"},
        {"measurement_definition": "dispatch_plus_travel"},
        {"method_source_url": None},
        {"method_edition_date": None},
        {"method_source_url": "file:///tmp/method"},
    ],
)
def test_malformed_fire_evidence_is_rejected_without_coercion(changes: dict[str, object]) -> None:
    constructor = cast(Callable[..., FireFacts], FireFacts)
    with pytest.raises((TypeError, ValueError)):
        constructor(**{**asdict(facts()), **changes})


def test_boolean_speed_cannot_become_a_one_kilometre_per_hour_profile() -> None:
    with pytest.raises(InvalidQuery):
        FireProfile(True, "Invalid boolean speed")


def test_verified_population_requires_a_confirmed_disjoint_partition() -> None:
    constructor = cast(Callable[..., FireFacts], FireFacts)
    with pytest.raises(ValueError, match="disjoint partition"):
        constructor(**{**asdict(facts()), "population_partition_verified": False})
