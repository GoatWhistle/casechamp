from dataclasses import replace

import pytest

from app.domain.normative.model import AccessRow
from app.domain.normative.territory import (
    ENCODED_PARENT_STATUS,
    TerritoryContext,
    apply_library_conditions,
    library_threshold,
)


def row(key: str = "city") -> AccessRow:
    return AccessRow(key, "Place", 100, 55, 65, "library", 30, 0, "within")


def test_library_threshold_depends_on_municipality_not_settlement_type() -> None:
    assert library_threshold("urban_okrug") == 40
    assert library_threshold("municipal_okrug") == 60
    assert library_threshold(None) is None


def test_unknown_territory_does_not_inherit_the_catalog_default_threshold() -> None:
    result = apply_library_conditions([row()], [])[0]
    assert result.threshold_minutes is None
    assert result.state == "unknown"
    assert result.minutes == 30
    assert result.population == 100
    assert "territory_conditions_missing" in result.uncertainty


def test_verified_municipality_does_not_prove_the_transport_profile() -> None:
    context = TerritoryContext("city", "urban_okrug", "primary-source", "primary_verified")
    result = apply_library_conditions([row()], [context])[0]
    assert result.threshold_minutes == 40
    assert result.territory_source_url == "primary-source"
    assert "territory_conditions_missing" not in result.uncertainty
    assert "transport_mode_unconfirmed" in result.uncertainty
    assert result.state == "unknown"
    assert result.excess_minutes is None


def test_candidate_context_does_not_become_verified_and_keeps_missing_path() -> None:
    context = TerritoryContext("city", "municipal_okrug", "osm-source", "candidate")
    original = replace(row(), minutes=None, facility_id=None)
    result = apply_library_conditions([original], [context])[0]
    assert result.threshold_minutes == 60
    assert result.minutes is None
    assert result.state == "unknown"
    assert "territory_conditions_missing" in result.uncertainty
    assert original.threshold_minutes is None


def test_ambiguous_context_is_rejected_instead_of_last_row_winning() -> None:
    context = TerritoryContext("city", "urban_okrug", "source", "primary_verified")
    with pytest.raises(ValueError, match="Conflicting"):
        apply_library_conditions([row()], [context, context])


def test_encoded_parent_threshold_keeps_assignment_unknown_and_freezes_its_sources() -> None:
    context = TerritoryContext(
        "37502000101",
        "municipal_okrug",
        "reference-2024",
        ENCODED_PARENT_STATUS,
        "37502000",
        "coding-rule",
    )
    result = apply_library_conditions([row(context.point_id)], [context])[0]
    assert result.threshold_minutes == 60
    assert result.state == "unknown"
    assert result.territory_verification_status == ENCODED_PARENT_STATUS
    assert result.municipality_code == "37502000"
    assert result.territory_structure_source_url == "coding-rule"
    assert "territory_conditions_missing" in result.uncertainty


def test_encoded_context_rejects_a_different_parent_code() -> None:
    with pytest.raises(ValueError, match="exact parent"):
        TerritoryContext(
            "37502000101",
            "municipal_okrug",
            "source",
            ENCODED_PARENT_STATUS,
            "37504000",
            "coding-rule",
        )
