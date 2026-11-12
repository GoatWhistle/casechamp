from collections.abc import Callable
from dataclasses import replace
from datetime import datetime
from typing import cast
from unittest.mock import Mock

import pytest
from tests.unit.adapter.normative.test_normative_routing import setup_routing
from tests.unit.domain.normative.library.factories import INSTANT, criterion, facts

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
        origin_latitude=55.2,
        routing_node=2,
        measurement_graph_revision="test",
    )
    repository = Mock(spec=NormativeRepository)
    repository.criteria.return_value = [criterion()]
    repository.facilities.return_value = [
        replace(target, service="library", coordinate_status="verified_entrance"),
    ]
    repository.origins.return_value = origins[:1]
    repository.territories.return_value = []
    repository.library_facts.return_value = [evidence]
    repository.save.return_value = AssessmentReceipt("run", INSTANT)
    usecase = NormativeQueries(
        cast(NormativeRepository, repository),
        routing,
        clock=lambda: INSTANT,
    )
    return usecase, repository


def test_real_routing_qualifies_baseline_and_keeps_unverified_closure_unknown() -> None:
    usecase, repository = configured()
    result = usecase.assess("N07", [10])
    assert result.baseline_rows[0].state == "within"
    assert result.rows[0].state == "unknown"
    assert result.rows[0].minutes == 90
    assert "scenario_conditions_unconfirmed" in result.rows[0].uncertainty
    assert result.baseline.lower_percent == 100
    assert result.scenario.lower_percent == 0
    assert result.scenario.upper_percent == 100
    saved = repository.save.call_args.args[0]
    assert saved.library_facts == tuple(repository.library_facts.return_value)
    assert saved.qualification_as_of == INSTANT
    assert result.saved_at == INSTANT


def test_inconsistent_population_cohorts_fail_before_persistence() -> None:
    usecase, repository = configured()
    origin = repository.origins.return_value[0]
    repository.origins.return_value.append(replace(origin, id="other"))
    evidence = repository.library_facts.return_value[0]
    repository.library_facts.return_value.append(
        replace(evidence, origin_id="other", population_reference="another-cohort"),
    )
    with pytest.raises(DataUnavailable, match="inconsistent"):
        usecase.assess("N07", [])
    repository.save.assert_not_called()


@pytest.mark.parametrize("clock", [None, lambda: INSTANT.replace(tzinfo=None)])
def test_evidence_without_an_explicit_aware_clock_cannot_be_saved(
    clock: Callable[[], datetime] | None,
) -> None:
    usecase, repository = configured()
    usecase.clock = clock
    with pytest.raises(DataUnavailable, match="clock"):
        usecase.assess("N07", [])
    repository.save.assert_not_called()


def test_decision_clock_is_normalized_once_to_storage_milliseconds() -> None:
    usecase, repository = configured()
    clock = Mock(return_value=INSTANT.replace(microsecond=123456))
    usecase.clock = clock
    result = usecase.assess("N07", [])
    assert result.qualification_as_of == INSTANT.replace(microsecond=123000)
    clock.assert_called_once_with()
    repository.save.assert_called_once()
