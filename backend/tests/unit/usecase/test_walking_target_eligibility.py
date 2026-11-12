from dataclasses import replace

from tests.unit.adapter.normative.test_walking_routing import NetworkRepository, facility, origin
from tests.unit.domain.normative.test_walking_rules import facts

from app.adapter.normative.walking_routing import WalkingNormativeRouting
from app.usecase.normative.walking_evaluation import evaluate_walking_targets


def test_a_nearer_ineligible_target_does_not_replace_the_confirmed_school() -> None:
    routing = WalkingNormativeRouting(NetworkRepository())
    far = replace(facility(), id="far")
    near = replace(facility(), id="near", longitude=65.0001)
    context = replace(
        facts(), origin_id=origin().id, facility_id="far", eligible_facility_ids=("far",)
    )
    result = evaluate_walking_targets(routing, [origin()], [near, far], 500, [], [context])
    assert result[0].facility_id == "far"
    assert result[0].distance_metres == 20
    proxy = evaluate_walking_targets(routing, [origin()], [near, far], 500, [], [])
    assert proxy[0].facility_id == "near"


def test_closure_uses_another_confirmed_target_and_missing_catalog_entries_stay_unknown() -> None:
    routing = WalkingNormativeRouting(NetworkRepository())
    far = replace(facility(), id="far")
    near = replace(facility(), id="near", longitude=65.0001)
    context = replace(facts(), origin_id=origin().id, eligible_facility_ids=("near", "far"))
    result = evaluate_walking_targets(routing, [origin()], [near, far], 500, [12], [context])
    assert result[0].facility_id == "near"
    assert result[0].distance_metres == 10
    missing = replace(context, eligible_facility_ids=("missing",))
    unknown = evaluate_walking_targets(routing, [origin()], [near, far], 500, [], [missing])[0]
    assert unknown.facility_id is None
    assert unknown.distance_metres is None
    assert unknown.state == "unknown"
