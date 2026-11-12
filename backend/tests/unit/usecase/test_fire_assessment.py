from dataclasses import replace
from typing import cast
from unittest.mock import Mock

import numpy as np
import pytest
from tests.unit.adapter.normative.test_normative_routing import setup_routing
from tests.unit.domain.normative.fire_evidence.factories import criterion, facts, profile
from tests.unit.domain.normative.library.factories import INSTANT

from app.adapter.normative.fire_routing import FireRoutingFactory
from app.domain.errors import DataUnavailable
from app.usecase.normative.dto import AssessmentReceipt
from app.usecase.normative.interface import NormativeRepository
from app.usecase.normative.queries import NormativeQueries


def configured() -> tuple[NormativeQueries, Mock]:
    road, origins, target = setup_routing()
    road.base.data.edges["km"] = np.array([4.0, 8.0, 20.0])
    evidence = replace(
        facts(),
        origin_id="a",
        eligible_facility_ids=("f",),
        origin_latitude=55.2,
        routing_node=2,
        measurement_graph_revision="test",
    )
    far = replace(target, service="fire", coordinate_status="verified_fire_exit")
    near = replace(far, id="near", latitude=55.2)
    repository = Mock(spec=NormativeRepository)
    repository.criteria.return_value = [criterion()]
    repository.facilities.return_value = [near, far]
    repository.origins.return_value = origins[:1]
    repository.fire_facts.return_value = [evidence]
    repository.settlement_types.return_value = []
    repository.save.return_value = AssessmentReceipt("run", INSTANT)
    return NormativeQueries(
        cast(NormativeRepository, repository),
        road,
        fire=FireRoutingFactory(road.base),
        clock=lambda: INSTANT,
    ), repository


def test_real_fire_routing_excludes_nearer_ineligible_depot_and_compares_the_call_limit() -> None:
    usecase, repository = configured()
    result = usecase.assess("N03", [], profile())
    point = result.rows[0]
    assert (point.facility_id, point.minutes, point.state) == ("f", 12, "exceeded")
    assert (point.threshold_minutes, point.excess_minutes, point.population) == (10, 2, 100)
    assert result.scenario.exceeded == 100
    saved = repository.save.call_args.args[0]
    assert saved.fire_facts == tuple(repository.fire_facts.return_value)
    assert saved.qualification_as_of == INSTANT
    assert saved.facilities[1].coordinate_status == "verified_fire_exit"
    repository.fire_facts.return_value = [
        replace(repository.fire_facts.return_value[0], settlement_type="rural")
    ]
    assert usecase.assess("N03", [], profile()).rows[0].state == "within"


def test_changed_speed_or_description_cannot_reuse_an_attested_profile() -> None:
    usecase, _ = configured()
    for changed in [
        replace(profile(), speed_kmh=40),
        replace(profile(), assumption="Another weather assumption"),
    ]:
        result = usecase.assess("N03", [], changed)
        assert result.rows[0].state == "unknown"
        assert "fire_speed_assumed" in result.rows[0].uncertainty


def test_empty_eligible_list_does_not_fall_back_and_unattached_depot_prevents_failure() -> None:
    usecase, repository = configured()
    evidence = repository.fire_facts.return_value[0]
    repository.fire_facts.return_value = [replace(evidence, eligible_facility_ids=("absent",))]
    missing = usecase.assess("N03", [], profile()).rows[0]
    assert missing.state == "unknown" and missing.minutes is None and missing.facility_id is None
    depot = repository.facilities.return_value[1]
    repository.facilities.return_value.append(
        replace(depot, id="absent", latitude=None, longitude=None)
    )
    repository.fire_facts.return_value = [replace(evidence, eligible_facility_ids=("f", "absent"))]
    partial = usecase.assess("N03", [], profile()).rows[0]
    assert partial.minutes == 12 and partial.state == "unknown"


def test_closure_needs_attestation_and_trace_runs_from_depot_to_object() -> None:
    usecase, repository = configured()
    result = usecase.assess("N03", [10], profile())
    assert result.baseline_rows[0].state == "exceeded"
    assert result.rows[0].minutes == 28 and result.rows[0].state == "unknown"
    evidence = repository.fire_facts.return_value[0]
    repository.fire_facts.return_value = [
        replace(evidence, scenario_verified=True, verified_closed_way_ids=(10,))
    ]
    confirmed = usecase.assess("N03", [10], profile())
    assert confirmed.rows[0].state == "exceeded"
    assert confirmed.rows[0].excess_minutes == 18
    assert usecase.fire is not None
    routing = usecase.fire.with_profile(profile())
    trace = routing.trace(
        repository.origins.return_value[0], repository.facilities.return_value[1], [10], "test"
    )
    assert trace.minutes == 28
    assert trace.network_coordinates == [(65, 55), (65, 55.1), (65, 55.2)]


def test_population_cohort_conflict_fails_before_save() -> None:
    usecase, repository = configured()
    repository.origins.return_value.append(replace(repository.origins.return_value[0], id="other"))
    repository.fire_facts.return_value.append(
        replace(
            repository.fire_facts.return_value[0], origin_id="other", population_reference="other"
        )
    )
    with pytest.raises(DataUnavailable, match="inconsistent"):
        usecase.assess("N03", [], profile())
    repository.save.assert_not_called()
