from dataclasses import replace

from tests.unit.adapter.normative.test_normative_routing import setup_routing
from tests.unit.domain.normative.library.factories import INSTANT, criterion, facts

from app.domain.normative.library.qualification import apply_library_evidence
from app.usecase.normative.library_evaluation import evaluate_library_targets


def test_nearest_ineligible_library_is_excluded_and_verified_urban_limit_is_used() -> None:
    routing, origins, target = setup_routing()
    far = replace(target, service="library", coordinate_status="verified_entrance")
    near = replace(far, id="near", latitude=55.2)
    evidence = replace(
        facts(),
        origin_id="a",
        eligible_facility_ids=("f",),
        municipality_type="urban_okrug",
        origin_latitude=55.2,
        routing_node=2,
        measurement_graph_revision="test",
    )
    raw = evaluate_library_targets(routing, origins[:1], [near, far], 60, [], [evidence], INSTANT)
    assert raw[0].facility_id == "f"
    assert raw[0].minutes == 60
    assert raw[0].state == "exceeded"
    qualified = apply_library_evidence(
        criterion(),
        raw,
        [],
        [evidence],
        [near, far],
        "test",
        INSTANT,
        [],
    )[0]
    assert (qualified.state, qualified.threshold_minutes, qualified.excess_minutes) == (
        "exceeded",
        40,
        20,
    )
    assert far.coordinate_status == "verified_entrance"


def test_missing_eligible_target_never_falls_back_to_the_nearest_catalog_entry() -> None:
    routing, origins, target = setup_routing()
    evidence = replace(facts(), origin_id="a", eligible_facility_ids=("missing",))
    result = evaluate_library_targets(routing, origins, [target], 60, [], [evidence], INSTANT)
    assert result[0].facility_id is None
    assert result[0].minutes is None
    assert result[0].state == "unknown"
    assert [point.id for point in result] == ["a", "b"]


def test_an_unattached_inventory_member_prevents_a_false_negative() -> None:
    routing, origins, target = setup_routing()
    attached = replace(target, service="library", coordinate_status="verified_entrance")
    missing = replace(attached, id="missing", latitude=None, longitude=None)
    evidence = replace(facts(), origin_id="a", eligible_facility_ids=("f", "missing"))
    result = evaluate_library_targets(
        routing,
        origins,
        [attached, missing],
        60,
        [10],
        [evidence],
        INSTANT,
    )
    assert result[0].minutes == 90
    assert result[0].state == "unknown"


def test_expired_evidence_does_not_restrict_the_physical_scenario() -> None:
    routing, origins, target = setup_routing()
    expired = replace(facts(), origin_id="a", valid_until="2026-11-11")
    result = evaluate_library_targets(routing, origins, [target], 60, [], [expired], INSTANT)
    assert result[0].facility_id == "f"
    assert result[0].minutes == 60
