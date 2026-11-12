from collections.abc import Callable
from dataclasses import asdict
from typing import cast

import pytest
from tests.unit.domain.normative.medical.factories import facts

from app.domain.normative.medical.facts import MedicalFacts


@pytest.mark.parametrize(
    "changes",
    [
        {"service": "cardiology"},
        {"population_group": None},
        {"population_group": "children"},
        {"population": True},
        {"catchment_source_url": None},
        {"regional_adjustment_source_url": None},
        {"threshold_minutes": None},
        {"threshold_minutes": float("nan")},
        {"threshold_minutes": 0},
        {"threshold_minutes": True},
        {"ownership_scope_verified": "true"},
        {"facility_form_verified": 1},
        {"adult_profile_verified": None},
        {"catchment_source_url": "file:///tmp/proof"},
        {"regional_adjustment_source_url": "not-a-url"},
    ],
)
def test_malformed_medical_attestation_is_rejected(changes: dict[str, object]) -> None:
    constructor = cast(Callable[..., MedicalFacts], MedicalFacts)
    with pytest.raises((TypeError, ValueError)):
        constructor(**{**asdict(facts()), **changes})
