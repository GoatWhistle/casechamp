from dataclasses import replace

import pytest
from tests.unit.domain.normative.library.factories import INSTANT
from tests.unit.domain.normative.medical.factories import criterion, facility, facts, row

from app.domain.normative.medical.facts import MedicalFacts
from app.domain.normative.medical.qualification import apply_medical_evidence
from app.domain.normative.model import AccessRow, coverage


def qualify(point: AccessRow | None = None, evidence: MedicalFacts | None = None) -> AccessRow:
    return apply_medical_evidence(
        criterion(),
        [point or row()],
        [evidence or facts()],
        [facility()],
        "network",
        INSTANT,
        [],
    )[0]


def test_adult_population_replaces_whole_population_and_qualification_is_auditable() -> None:
    result = qualify()
    assert result.state == "within"
    assert result.population == 100
    assert result.threshold_minutes == 60
    assert result.uncertainty == ()
    assert result.qualification_source_url == facts().source_url
    assert result.qualification_observed_at == facts().observed_at
    assert coverage([result]).lower_percent == 100


def test_verified_adjustment_changes_threshold_without_changing_federal_catalog() -> None:
    evidence = replace(facts(), threshold_minutes=45)
    assert qualify(replace(row(), minutes=45), evidence).state == "within"
    result = qualify(replace(row(), minutes=46, state="exceeded"), evidence)
    assert (result.state, result.threshold_minutes, result.excess_minutes) == ("exceeded", 45, 1)
    assert criterion().threshold == 60


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
        (replace(facts(), ownership_scope_verified=False), "ownership_scope_unconfirmed"),
        (replace(facts(), ownership_applicable=None), "ownership_scope_unconfirmed"),
        (replace(facts(), regional_adjustment_verified=False), "regional_adjustment_unconfirmed"),
        (replace(facts(), transport_method_verified=False), "transport_mode_unconfirmed"),
        (replace(facts(), transport_mode=None), "transport_mode_unconfirmed"),
        (replace(facts(), facility_form_verified=False), "medical_form_unconfirmed"),
        (replace(facts(), adult_profile_verified=False), "adult_profile_unconfirmed"),
        (replace(facts(), catchment_verified=False), "medical_catchment_unconfirmed"),
        (replace(facts(), service_eligible=False), "facility_profile_unconfirmed"),
        (replace(facts(), service_active=False), "service_status_unconfirmed"),
        (replace(facts(), origin_reference_verified=False), "reference_location_unconfirmed"),
        (replace(facts(), routing_node=1), "reference_location_unconfirmed"),
        (replace(facts(), origin_latitude=56), "reference_location_unconfirmed"),
        (replace(facts(), approach_metres=1), "reference_location_unconfirmed"),
        (replace(facts(), measurement_verified=False), "measurement_version_unconfirmed"),
        (replace(facts(), measurement_graph_revision="old"), "measurement_version_unconfirmed"),
    ],
)
def test_unverified_conditions_cannot_qualify_medical_access(
    evidence: MedicalFacts, reason: str
) -> None:
    result = qualify(evidence=evidence)
    assert result.state == "unknown"
    assert result.excess_minutes is None
    assert reason in result.uncertainty


def test_unknown_or_partial_adult_population_never_uses_whole_population_as_a_weight() -> None:
    result = apply_medical_evidence(
        criterion(),
        [row(), replace(row(), id="other")],
        [facts()],
        [facility()],
        "network",
        INSTANT,
        [],
    )
    assert [r.population for r in result] == [100, None]
    assert coverage(result).lower_percent is None
    assert qualify(evidence=replace(facts(), population_verified=False)).population is None
    result = apply_medical_evidence(criterion(), [row()], [], [facility()], "network", None, [])
    assert result[0].state == "unknown" and result[0].population is None


def test_other_care_form_and_mixed_population_cohort_are_rejected() -> None:
    with pytest.raises(ValueError, match="care form"):
        qualify(evidence=facts("urgent_cardiology"))
    with pytest.raises(ValueError, match="references"):
        apply_medical_evidence(
            criterion(),
            [row(), replace(row(), id="other")],
            [facts(), replace(facts(), origin_id="other", population_reference="other-cohort")],
            [facility()],
            "network",
            INSTANT,
            [],
        )


def test_partial_inventory_can_prove_access_but_not_a_negative_conclusion() -> None:
    partial = replace(facts(), eligible_inventory_complete=False)
    assert qualify(evidence=partial).state == "within"
    assert qualify(replace(row(), minutes=61, state="exceeded"), partial).state == "unknown"
    assert qualify(replace(row(), minutes=None, state="unreachable"), partial).state == "unknown"
    assert qualify(replace(row(), minutes=61, state="exceeded")).state == "exceeded"
    assert qualify(replace(row(), minutes=None, state="unreachable")).state == "unreachable"


def test_out_of_scope_cases_are_counted_separately_from_failure() -> None:
    for evidence in [
        replace(facts(), ownership_applicable=False),
        replace(facts(), planning_scope=False),
    ]:
        result = qualify(evidence=evidence)
        assert result.state == "not_applicable"
        summary = coverage([result])
        assert summary.population == 0
        assert summary.not_applicable_population == 100


def test_scenario_attestation_matches_the_exact_closure_set() -> None:
    for evidence, state in [
        (facts(), "unknown"),
        (replace(facts(), scenario_verified=True, verified_closed_way_ids=(11,)), "unknown"),
        (replace(facts(), scenario_verified=True, verified_closed_way_ids=(12,)), "within"),
    ]:
        result = apply_medical_evidence(
            criterion(),
            [row()],
            [evidence],
            [facility()],
            "network",
            INSTANT,
            [12],
        )[0]
        assert result.state == state


def test_building_coordinates_or_wrong_care_form_do_not_become_verified_entrances() -> None:
    for target in [
        replace(facility(), coordinate_status="osm_building"),
        facility("urgent_cardiology"),
    ]:
        for point in [row(), replace(row(), minutes=None, state="unreachable")]:
            result = apply_medical_evidence(
                criterion(),
                [point],
                [facts()],
                [target],
                "network",
                INSTANT,
                [],
            )[0]
            assert result.state == "unknown"


@pytest.mark.parametrize(
    "service,limit", [("emergency_cardiology", 60), ("urgent_cardiology", 120)]
)
def test_care_forms_keep_their_own_verified_thresholds(service: str, limit: int) -> None:
    result = apply_medical_evidence(
        criterion(service),
        [replace(row(), minutes=90, state="exceeded" if limit == 60 else "within")],
        [facts(service)],
        [facility(service)],
        "network",
        INSTANT,
        [],
    )[0]
    assert result.state == ("exceeded" if limit == 60 else "within")
    assert result.threshold_minutes == limit
