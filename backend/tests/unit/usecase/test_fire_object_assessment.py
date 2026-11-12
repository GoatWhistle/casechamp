from dataclasses import replace
from unittest.mock import Mock

import pytest
from tests.unit.domain.normative.fire_destination.test_destination import destination
from tests.unit.domain.normative.fire_evidence.factories import facts, profile
from tests.unit.usecase.test_fire_assessment import configured

from app.adapter.normative.origin_attachment import GraphOriginAttachment
from app.adapter.normative.routing import GraphNormativeRouting
from app.domain.errors import DataUnavailable, InvalidQuery
from app.domain.normative.model import Origin
from app.usecase.normative.queries import NormativeQueries


def objects() -> tuple[NormativeQueries, Mock]:
    usecase, repository = configured()
    assert isinstance(usecase.routing, GraphNormativeRouting)
    attachment = GraphOriginAttachment(usecase.routing.base)
    usecase.object_attachment = attachment
    target = destination()
    repository.fire_destinations.return_value = [target]
    attached = attachment.attach(
        [Origin(target.id, target.name, None, None, None, target.latitude, target.longitude)],
        "test",
    )[0]
    assert attached.snap_km is not None
    repository.fire_facts.return_value = [
        replace(
            facts(),
            origin_id=target.id,
            origin_latitude=target.latitude,
            origin_longitude=target.longitude,
            routing_node=attached.node,
            approach_metres=attached.snap_km * 1000,
            eligible_facility_ids=("f",),
            measurement_graph_revision="test",
        )
    ]
    return usecase, repository


def test_arbitrary_objects_replace_settlement_origins_without_mutating_them() -> None:
    usecase, repository = objects()
    before = list(repository.origins.return_value)
    result = usecase.assess("N03", [], profile(), "fire_objects")
    assert result.origin_basis == "fire_objects"
    assert len(result.rows) == 1 and result.rows[0].id == "site-42"
    point = result.rows[0]
    assert point.routing_node == 1
    assert point.minutes is not None and 4 < point.minutes < 4.01
    assert (point.state, point.population) == ("within", 100)
    assert point.origin_source_url == destination().source_url
    assert point.origin_source_sha256 == destination().source_sha256
    assert result.fire_destinations == (destination(),)
    assert repository.origins.return_value == before
    repository.origins.assert_not_called()
    assert repository.save.call_args.args[0].origin_basis == "fire_objects"


def test_candidate_reference_does_not_become_verified_through_a_fact_flag() -> None:
    usecase, repository = objects()
    repository.fire_destinations.return_value = [
        replace(destination(), reference_status="candidate_point")
    ]
    result = usecase.assess("N03", [], profile(), "fire_objects")
    assert result.rows[0].state == "unknown"
    assert "fire_destination_unconfirmed" in result.rows[0].uncertainty


def test_empty_object_registry_never_falls_back_to_settlement_centres() -> None:
    usecase, repository = objects()
    repository.fire_destinations.return_value = []
    with pytest.raises(DataUnavailable, match="No sourced"):
        usecase.assess("N03", [], profile(), "fire_objects")
    repository.origins.assert_not_called()
    repository.save.assert_not_called()


def test_missing_facts_keep_object_population_unknown_instead_of_using_settlement_weights() -> None:
    usecase, repository = objects()
    repository.fire_facts.return_value = []
    result = usecase.assess("N03", [], profile(), "fire_objects")
    assert result.rows[0].population is None and result.rows[0].state == "unknown"
    assert result.scenario.lower_percent is None


def test_cross_region_registry_is_rejected_before_save() -> None:
    usecase, repository = objects()
    repository.fire_destinations.return_value = [replace(destination(), region="Other")]
    with pytest.raises(DataUnavailable, match="region"):
        usecase.assess("N03", [], profile(), "fire_objects")
    repository.save.assert_not_called()


def test_object_basis_does_not_apply_to_other_criteria() -> None:
    usecase, repository = objects()
    repository.criteria.return_value = [
        replace(repository.criteria.return_value[0], id="N05", service="mfc", mode="car")
    ]
    with pytest.raises(InvalidQuery, match="only apply"):
        usecase.assess("N05", [], origin_basis="fire_objects")
    repository.save.assert_not_called()
