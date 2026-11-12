from dataclasses import replace
from typing import cast
from unittest.mock import Mock

import pytest
from tests.unit.adapter.normative.test_normative_routing import setup_routing
from tests.unit.domain.normative.library.factories import INSTANT
from tests.unit.domain.normative.medical.factories import criterion, facts

from app.domain.errors import DataUnavailable
from app.usecase.normative.dto import AssessmentReceipt
from app.usecase.normative.interface import NormativeRepository
from app.usecase.normative.queries import NormativeQueries


def configured() -> tuple[NormativeQueries, Mock]:
    routing, origins, target = setup_routing()
    evidence = replace(
        facts(),
        origin_id="a",
        eligible_facility_ids=("f",),
        threshold_minutes=45,
        origin_latitude=55.2,
        routing_node=2,
        measurement_graph_revision="test",
    )
    far = replace(target, service=criterion().service, coordinate_status="verified_entrance")
    near = replace(far, id="near", latitude=55.2)
    repository = Mock(spec=NormativeRepository)
    repository.criteria.return_value = [criterion()]
    repository.facilities.return_value = [near, far]
    repository.origins.return_value = origins[:1]
    repository.medical_facts.return_value = [evidence]
    repository.save.return_value = AssessmentReceipt("run", INSTANT)
    return NormativeQueries(
        cast(NormativeRepository, repository), routing, clock=lambda: INSTANT
    ), repository


def test_actual_routing_excludes_ineligible_nearby_clinic_and_uses_adjusted_threshold() -> None:
    usecase, repository = configured()
    result = usecase.assess("N01", [])
    point = result.rows[0]
    assert (point.facility_id, point.minutes, point.state) == ("f", 60, "exceeded")
    assert (point.population, point.threshold_minutes, point.excess_minutes) == (100, 45, 15)
    assert result.scenario.exceeded == 100
    assert result.scenario.lower_percent == 0
    saved = repository.save.call_args.args[0]
    assert saved.medical_facts == tuple(repository.medical_facts.return_value)
    assert saved.qualification_as_of == INSTANT
    assert result.criterion.threshold == 60


def test_missing_or_expired_facts_retain_whole_population_unknown_and_no_percentage() -> None:
    for expired in (False, True):
        usecase, repository = configured()
        repository.medical_facts.return_value = (
            [replace(repository.medical_facts.return_value[0], valid_until="2026-11-11")]
            if expired
            else []
        )
        result = usecase.assess("N01", [])
        assert result.rows[0].population is None
        assert result.rows[0].state == "unknown"
        assert result.scenario.lower_percent is None
        assert result.rows[0].facility_id == "near"


def test_missing_eligible_clinic_does_not_fall_back_to_nearest_other_clinic() -> None:
    usecase, repository = configured()
    repository.medical_facts.return_value = [
        replace(repository.medical_facts.return_value[0], eligible_facility_ids=("absent",)),
    ]
    result = usecase.assess("N01", [])
    assert result.rows[0].facility_id is None
    assert result.rows[0].minutes is None
    assert result.rows[0].state == "unknown"


def test_other_care_form_and_mixed_cohorts_fail_without_saving() -> None:
    for wrong_form in (False, True):
        usecase, repository = configured()
        evidence = repository.medical_facts.return_value[0]
        if wrong_form:
            repository.medical_facts.return_value = [replace(evidence, service="urgent_cardiology")]
        else:
            repository.origins.return_value.append(
                replace(repository.origins.return_value[0], id="other")
            )
            repository.medical_facts.return_value.append(
                replace(evidence, origin_id="other", population_reference="other-cohort"),
            )
        with pytest.raises(DataUnavailable, match="inconsistent"):
            usecase.assess("N01", [])
        repository.save.assert_not_called()


def test_baseline_does_not_qualify_a_changed_network_without_scenario_evidence() -> None:
    usecase, repository = configured()
    evidence = replace(repository.medical_facts.return_value[0], threshold_minutes=60)
    repository.medical_facts.return_value = [evidence]
    result = usecase.assess("N01", [10])
    assert result.baseline_rows[0].state == "within"
    assert result.rows[0].state == "unknown"
    assert result.rows[0].minutes == 90
    assert "scenario_conditions_unconfirmed" in result.rows[0].uncertainty
    repository.medical_facts.return_value = [
        replace(evidence, scenario_verified=True, verified_closed_way_ids=(10,)),
    ]
    confirmed = usecase.assess("N01", [10])
    assert confirmed.rows[0].state == "exceeded"
    assert confirmed.rows[0].excess_minutes == 30
