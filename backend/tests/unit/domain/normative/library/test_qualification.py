from dataclasses import replace

import pytest
from tests.unit.domain.normative.library.factories import INSTANT, criterion, facility, facts, row

from app.domain.normative.library.facts import LibraryFacts
from app.domain.normative.library.qualification import apply_library_evidence
from app.domain.normative.model import AccessRow, Facility, coverage
from app.domain.normative.territory import TerritoryContext


def qualify(point: AccessRow | None = None, evidence: LibraryFacts | None = None) -> AccessRow:
    return apply_library_evidence(
        criterion(),
        [point or row()],
        [],
        [evidence or facts()],
        [facility()],
        "network",
        INSTANT,
        [],
    )[0]


def test_verified_evidence_uses_its_own_population_and_freezes_provenance() -> None:
    result = qualify()
    assert (result.state, result.population, result.threshold_minutes) == ("within", 100, 60)
    assert result.excess_minutes == 0
    assert result.qualification_source_url == facts().source_url
    assert result.qualification_observed_at == "2026-11-10"
    assert result.territory_verification_status == "verified_library_jurisdiction"
    assert result.uncertainty == ()
    assert coverage([result]).lower_percent == 100


def test_boundary_and_excess_use_verified_municipality_category() -> None:
    urban = replace(facts(), municipality_type="urban_okrug")
    assert qualify(replace(row(), minutes=40), urban).state == "within"
    result = qualify(replace(row(), minutes=41, state="exceeded"), urban)
    assert (result.state, result.excess_minutes) == ("exceeded", 1)
    assert qualify(replace(row(), minutes=41), urban).state == "unknown"


def test_partial_inventory_can_prove_access_but_cannot_prove_failure() -> None:
    partial = replace(facts(), eligible_inventory_complete=False)
    assert qualify(evidence=partial).state == "within"
    result = qualify(replace(row(), minutes=61, state="exceeded"), partial)
    assert result.state == "unknown"
    assert "inventory_incomplete" in result.uncertainty
    assert qualify(replace(row(), minutes=None, state="unreachable"), partial).state == "unknown"
    assert qualify(replace(row(), minutes=None, state="unreachable")).state == "unreachable"


@pytest.mark.parametrize(
    "evidence,reason",
    [
        (replace(facts(), facts_verified=False), "qualification_unconfirmed"),
        (replace(facts(), valid_until="2026-11-11"), "evidence_outside_validity"),
        (replace(facts(), observed_at="2026-11-13"), "evidence_outside_validity"),
        (replace(facts(), legal_currentness_verified=False), "normative_rule_unconfirmed"),
        (replace(facts(), legal_edition_date="2020-01-01"), "normative_rule_unconfirmed"),
        (
            replace(facts(), normative_source_url="https://example.org/other"),
            "normative_rule_unconfirmed",
        ),
        (replace(facts(), jurisdiction_verified=False), "territory_conditions_missing"),
        (replace(facts(), planning_scope=None), "planning_scope_unconfirmed"),
        (replace(facts(), transport_method_verified=False), "transport_mode_unconfirmed"),
        (replace(facts(), transport_mode=None), "transport_mode_unconfirmed"),
        (replace(facts(), origin_reference_verified=False), "reference_location_unconfirmed"),
        (replace(facts(), origin_latitude=56), "reference_location_unconfirmed"),
        (replace(facts(), routing_node=1), "reference_location_unconfirmed"),
        (replace(facts(), approach_metres=1), "reference_location_unconfirmed"),
        (replace(facts(), measurement_verified=False), "measurement_version_unconfirmed"),
        (replace(facts(), measurement_graph_revision="old"), "measurement_version_unconfirmed"),
        (replace(facts(), service_eligible=False), "facility_profile_unconfirmed"),
        (replace(facts(), service_active=False), "service_status_unconfirmed"),
    ],
)
def test_each_missing_attestation_keeps_the_status_unknown(
    evidence: LibraryFacts,
    reason: str,
) -> None:
    result = qualify(evidence=evidence)
    assert result.state == "unknown"
    assert reason in result.uncertainty
    assert result.excess_minutes is None


def test_nonapplicable_scope_is_excluded_from_the_population_denominator() -> None:
    for evidence in [replace(facts(), planning_scope=False), replace(facts(), territory="Other")]:
        result = qualify(evidence=evidence)
        assert result.state == "not_applicable"
        summary = coverage([result])
        assert summary.population == 0
        assert summary.not_applicable_population == 100
        assert summary.lower_percent is None


def test_missing_population_does_not_mix_a_verified_cohort_with_old_graph_weights() -> None:
    points = [row(), replace(row(), id="other")]
    result = apply_library_evidence(
        criterion(),
        points,
        [],
        [facts()],
        [facility()],
        "network",
        INSTANT,
        [],
    )
    assert [r.population for r in result] == [100, None]
    assert coverage(result).lower_percent is None
    assert "population_group_missing" in result[1].uncertainty
    assert qualify(evidence=replace(facts(), population_verified=False)).population is None


def test_population_cohorts_and_conflicting_verified_jurisdictions_are_rejected() -> None:
    with pytest.raises(ValueError, match="references"):
        apply_library_evidence(
            criterion(),
            [row(), replace(row(), id="other")],
            [],
            [facts(), replace(facts(), origin_id="other", population_reference="other-cohort")],
            [facility()],
            "network",
            INSTANT,
            [],
        )
    context = TerritoryContext("origin", "urban_okrug", "source", "primary_verified")
    with pytest.raises(ValueError, match="Conflicting"):
        apply_library_evidence(
            criterion(),
            [row()],
            [context],
            [facts()],
            [facility()],
            "network",
            INSTANT,
            [],
        )


def test_road_changes_require_exact_scenario_attestation() -> None:
    for evidence, expected in [
        (facts(), "unknown"),
        (replace(facts(), scenario_verified=True, verified_closed_way_ids=(11,)), "unknown"),
        (replace(facts(), scenario_verified=True, verified_closed_way_ids=(12,)), "within"),
    ]:
        result = apply_library_evidence(
            criterion(),
            [row()],
            [],
            [evidence],
            [facility()],
            "network",
            INSTANT,
            [12],
        )[0]
        assert result.state == expected


@pytest.mark.parametrize(
    "target",
    [
        replace(facility(), coordinate_status="osm_building"),
        replace(facility(), service="school"),
        replace(facility(), id="other"),
    ],
)
def test_unverified_or_ineligible_target_cannot_prove_compliance_or_unreachability(
    target: Facility,
) -> None:
    for point in [row(), replace(row(), minutes=None, state="unreachable")]:
        result = apply_library_evidence(
            criterion(),
            [point],
            [],
            [facts()],
            [target],
            "network",
            INSTANT,
            [],
        )[0]
        assert result.state == "unknown"
