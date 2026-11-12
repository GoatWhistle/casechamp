from dataclasses import replace

import pytest
from tests.unit.domain.normative.fire_evidence.factories import (
    criterion,
    facility,
    facts,
    profile,
    row,
)
from tests.unit.domain.normative.library.factories import INSTANT

from app.domain.normative.fire import SettlementContext
from app.domain.normative.fire_evidence.facts import FireFacts
from app.domain.normative.fire_evidence.qualification import apply_fire_evidence
from app.domain.normative.model import AccessRow, coverage


def qualify(point: AccessRow | None = None, evidence: FireFacts | None = None) -> AccessRow:
    return apply_fire_evidence(
        criterion(),
        [point or row()],
        [],
        [evidence or facts()],
        [facility()],
        "network",
        INSTANT,
        [],
        profile(),
    )[0]


def test_verified_object_and_population_are_qualified_with_frozen_sources() -> None:
    result = qualify()
    assert (result.state, result.threshold_minutes, result.population) == ("within", 10, 100)
    assert result.uncertainty == ()
    assert result.travel_profile_source_url == facts().speed_source_url
    assert result.measurement_method_source_url == facts().method_source_url
    assert coverage([result]).lower_percent == 100


@pytest.mark.parametrize(
    "evidence,reason",
    [
        (replace(facts(), facts_verified=False), "qualification_unconfirmed"),
        (replace(facts(), valid_until="2026-11-11"), "evidence_outside_validity"),
        (replace(facts(), observed_at="2026-11-13"), "evidence_outside_validity"),
        (replace(facts(), legal_currentness_verified=False), "normative_rule_unconfirmed"),
        (replace(facts(), method_currentness_verified=False), "normative_rule_unconfirmed"),
        (replace(facts(), legal_edition_date="2020-01-01"), "normative_rule_unconfirmed"),
        (replace(facts(), jurisdiction_verified=False), "territory_conditions_missing"),
        (replace(facts(), planning_scope=None), "planning_scope_unconfirmed"),
        (replace(facts(), settlement_type_verified=False), "territory_conditions_missing"),
        (replace(facts(), speed_verified=False), "fire_speed_assumed"),
        (replace(facts(), speed_kmh=40), "fire_speed_assumed"),
        (replace(facts(), profile_assumption="Different weather conditions"), "fire_speed_assumed"),
        (
            replace(facts(), adverse_conditions_verified=False),
            "fire_adverse_conditions_unconfirmed",
        ),
        (replace(facts(), vehicle_access_verified=False), "fire_vehicle_access_unconfirmed"),
        (replace(facts(), directionality_verified=False), "fire_directionality_unconfirmed"),
        (replace(facts(), operational_readiness_verified=False), "fire_readiness_unconfirmed"),
        (replace(facts(), destination_objects_verified=False), "fire_destination_unconfirmed"),
        (
            replace(facts(), measurement_definition_verified=False),
            "fire_measurement_definition_unconfirmed",
        ),
        (replace(facts(), transport_method_verified=False), "transport_mode_unconfirmed"),
        (replace(facts(), origin_reference_verified=False), "reference_location_unconfirmed"),
        (replace(facts(), origin_latitude=56), "reference_location_unconfirmed"),
        (replace(facts(), routing_node=1), "reference_location_unconfirmed"),
        (replace(facts(), measurement_graph_revision="old"), "measurement_version_unconfirmed"),
        (replace(facts(), service_eligible=False), "facility_profile_unconfirmed"),
        (replace(facts(), service_active=False), "service_status_unconfirmed"),
    ],
)
def test_each_unconfirmed_condition_blocks_fire_qualification(
    evidence: FireFacts, reason: str
) -> None:
    result = qualify(evidence=evidence)
    assert result.state == "unknown" and result.excess_minutes is None
    assert reason in result.uncertainty


def test_threshold_refers_to_the_call_destination_not_the_depot() -> None:
    assert qualify(replace(row(), minutes=15, state="exceeded")).state == "exceeded"
    rural = qualify(replace(row(), minutes=15), replace(facts(), settlement_type="rural"))
    assert (rural.state, rural.threshold_minutes) == ("within", 20)
    assert (
        qualify(replace(row(), minutes=20), replace(facts(), settlement_type="rural")).state
        == "within"
    )


def test_incomplete_inventory_cannot_prove_negative_access_or_disconnection() -> None:
    partial = replace(facts(), eligible_inventory_complete=False)
    assert qualify(evidence=partial).state == "within"
    assert qualify(replace(row(), minutes=11, state="exceeded"), partial).state == "unknown"
    assert qualify(replace(row(), minutes=None, state="unreachable"), partial).state == "unknown"
    assert qualify(replace(row(), minutes=None, state="unreachable")).state == "unreachable"


def test_population_unknown_is_not_replaced_with_all_residents() -> None:
    result = apply_fire_evidence(
        criterion(),
        [row(), replace(row(), id="other")],
        [],
        [facts()],
        [facility()],
        "network",
        INSTANT,
        [],
        profile(),
    )
    assert [r.population for r in result] == [100, None]
    assert coverage(result).lower_percent is None
    assert qualify(evidence=replace(facts(), population_verified=False)).population is None


def test_conflicting_verified_call_categories_are_rejected() -> None:
    previous = SettlementContext("origin", "rural", "source", "primary_verified")
    with pytest.raises(ValueError, match="Conflicting"):
        apply_fire_evidence(
            criterion(),
            [row()],
            [previous],
            [facts()],
            [facility()],
            "network",
            INSTANT,
            [],
            profile(),
        )


def test_closures_require_exact_attestation_and_buildings_are_not_verified_exits() -> None:
    for evidence, expected in [
        (facts(), "unknown"),
        (replace(facts(), scenario_verified=True, verified_closed_way_ids=(12,)), "within"),
    ]:
        result = apply_fire_evidence(
            criterion(), [row()], [], [evidence], [facility()], "network", INSTANT, [12], profile()
        )[0]
        assert result.state == expected
    for target in [
        replace(facility(), coordinate_status="verified_entrance"),
        replace(facility(), service="library"),
    ]:
        result = apply_fire_evidence(
            criterion(), [row()], [], [facts()], [target], "network", INSTANT, [], profile()
        )[0]
        assert result.state == "unknown"


def test_confirmed_nonapplicability_is_excluded_from_denominator() -> None:
    result = qualify(evidence=replace(facts(), planning_scope=False))
    assert result.state == "not_applicable"
    assert coverage([result]).not_applicable_population == 100
