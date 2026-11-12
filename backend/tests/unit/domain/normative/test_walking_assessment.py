from dataclasses import replace

import pytest
from tests.unit.domain.normative.test_walking_rules import facts, row

from app.domain.normative.model import Origin, coverage
from app.domain.normative.walking_assessment import apply_walking_conditions, walking_entrances


def test_missing_facts_share_one_frozen_rule_set_without_inventing_people() -> None:
    rows = [row(100), replace(row(None), id="other")]
    before, after, groups = apply_walking_conditions("school", rows, list(reversed(rows)), [])
    assert len(groups) == 1
    assert {r.rule_set_id for r in before + after} == {groups[0].id}
    assert coverage(after).lower_percent is None
    assert all(r.population is None and r.state == "unknown" for r in after)


def test_different_case_results_keep_stable_ids_and_do_not_mutate_the_inputs() -> None:
    a = replace(
        facts("stop"), population=10, population_group="residents", population_group_verified=True
    )
    b = replace(a, origin_id="other", zones=("city_centre",), population=0)
    rows = [row(700), replace(row(100), id="other")]
    before, after, groups = apply_walking_conditions("stop", rows, rows, [a, b])
    assert [r.state for r in after] == ["within", "within"]
    assert [r.population for r in after] == [10, 0]
    assert coverage(after).lower_percent == 100
    assert len(groups) == 2
    assert [group.id for group in groups] == sorted(group.id for group in groups)
    assert before == after
    assert all(r.rule_set_id is None and r.population is None for r in rows)


def test_verified_entrances_replace_coordinates_before_routing() -> None:
    original = Origin("o", "Building", None, None, None, 55, 65)
    entrance = replace(
        facts(), entrance_verified=True, entrance_latitude=55.001, entrance_longitude=65.002
    )
    prepared = walking_entrances([original], [entrance])[0]
    assert prepared.latitude == 55.001
    assert prepared.longitude == 65.002
    assert prepared.entrance_verified
    assert original.latitude == 55
    assert walking_entrances([original], [replace(entrance, facts_verified=False)]) == [original]


def test_contexts_cannot_silently_duplicate_or_mix_population_cohorts() -> None:
    with pytest.raises(ValueError, match="Conflicting"):
        apply_walking_conditions("school", [row()], [row()], [facts(), facts()])
    entrance = replace(
        facts(),
        entrance_verified=True,
        entrance_latitude=55,
        entrance_longitude=65,
        origin_kind="industrial_gate",
    )
    with pytest.raises(ValueError, match="population cohorts"):
        walking_entrances([Origin("o", "Building", None, None, None, 55, 65)], [entrance])


def test_unregulated_population_is_excluded_instead_of_becoming_unknown_or_zero_access() -> None:
    context = replace(
        facts("stop"),
        settlement_category="rural",
        population=90,
        population_group="residents",
        population_group_verified=True,
    )
    _, assessed, _ = apply_walking_conditions("stop", [row()], [row()], [context])
    assert assessed[0].state == "not_regulated"
    selected = replace(row(), id="numeric", state="within", population=10)
    result = coverage([selected, *assessed])
    assert result.population == 10
    assert result.not_regulated_population == 90
    assert result.not_regulated_points == 1
    assert result.unknown == 0
    assert result.lower_percent == 100


def test_excluded_missing_population_remains_missing_and_undated_law_stays_unknown() -> None:
    context = replace(facts("stop"), settlement_category="rural")
    _, assessed, _ = apply_walking_conditions("stop", [row()], [row()], [context])
    result = coverage(assessed)
    assert result.unknown_population_points == 0
    assert result.excluded_unknown_population_points == 1
    assert result.lower_percent is None
    _, uncertain, _ = apply_walking_conditions(
        "stop", [row()], [row()], [replace(context, legal_currentness_verified=False)]
    )
    assert uncertain[0].state == "unknown"


def test_baseline_service_evidence_is_not_silently_reused_after_a_closure() -> None:
    context = facts("stop")
    before, after, groups = apply_walking_conditions(
        "stop", [row(100)], [row(1500)], [context], [10]
    )
    assert before[0].state == "within"
    assert after[0].state == "unknown"
    scenario = next(group for group in groups if group.id == after[0].rule_set_id)
    assert scenario.checks[0].reason == "scenario_unverified"
    verified = replace(context, scenario_verified=True, verified_closed_way_ids=(10,))
    _, changed, _ = apply_walking_conditions("stop", [row(100)], [row(1500)], [verified], [10])
    assert changed[0].state == "exceeded"
    _, other_closure, _ = apply_walking_conditions(
        "stop", [row(100)], [row(1500)], [verified], [11]
    )
    assert other_closure[0].state == "unknown"


def test_measurement_proof_is_bound_to_the_assessed_network_revision() -> None:
    context = facts("stop")
    _, changed_network, groups = apply_walking_conditions(
        "stop", [row(100)], [row(100)], [context], graph_revision="other-network"
    )
    assert changed_network[0].state == "unknown"
    assert groups[0].checks[0].reason == "measurement_version_mismatch"
    _, verified, _ = apply_walking_conditions(
        "stop", [row(100)], [row(100)], [context], graph_revision="network"
    )
    assert verified[0].state == "within"
