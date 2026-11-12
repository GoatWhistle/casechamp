from unittest.mock import Mock

from app.adapter.road_graph.attachment_audit import SettlementAttachmentConflict
from app.adapter.road_graph.closure_validity import road_job_view, stress_job_view
from app.usecase.road_graph import RoadChange, RoadJob, RoadResult
from app.usecase.road_stress import StressJob, StressRegion


def test_invalid_saved_road_result_becomes_terminal_without_changing_the_original() -> None:
    original = RoadJob(
        "old",
        "07",
        "Region",
        "road",
        [RoadChange(1, 0)],
        "completed",
        360,
        360,
        "v",
        result=RoadResult(99, 98, -1, -1, 38614, 1, 4, 100, 0),
    )
    audit = Mock(validate=Mock(side_effect=SettlementAttachmentConflict(["city"])))
    view = road_job_view(original, audit)
    assert view.status == "failed" and view.result is None
    assert view.error == "settlement_attachment_conflict"
    assert original.status == "completed" and original.result is not None


def test_invalid_saved_stress_result_has_no_publishable_regional_consequences() -> None:
    original = StressJob(
        "old",
        "v",
        [1],
        status="completed",
        regions=[StressRegion("Region", 1, 38614, 38614)],
        newly_isolated_points=1,
    )
    audit = Mock(validate=Mock(side_effect=SettlementAttachmentConflict(["city"])))
    view = stress_job_view(original, audit)
    assert view.status == "failed" and not view.regions
    assert view.newly_isolated_points == 0
    assert original.regions[0].isolated_population == 38614
