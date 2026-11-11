import json
from unittest.mock import Mock

import pytest
from pydantic_ai import ModelRetry, RunContext

from app.adapter.chat.artifacts import ChatRun
from app.adapter.chat.road_tools import RoadTools
from app.domain.errors import DataUnavailable
from app.domain.transport import NetworkMode, Season
from app.usecase.chat import ChatContext
from app.usecase.road_graph import RoadChange, RoadJob


def test_speed_submission_emits_calculation_with_job_and_changes() -> None:
    graph = Mock()
    changes = [RoadChange(7, 1.2)]
    graph.submit.return_value = RoadJob(
        "speed", "1", "Region", "summer", changes, "queued", 0, 360, "test"
    )
    graph.geometry.return_value = Mock(
        names=["R-1"], length_km=4, lines=[[[40.0, 44.0], [41.0, 45.0]]]
    )
    run = ChatRun(ChatContext(None, Season.SUMMER, NetworkMode.ROAD, "hansen"))
    context = Mock(spec=RunContext, deps=run)
    RoadTools(graph).recalculate_road_index(context, "1", "summer", changes)
    assert len(run.pending) == 1
    calculation = run.pending[0].calculation
    assert calculation is not None
    assert calculation.job_ids == ["speed"]
    assert calculation.changes == changes
    assert calculation.corridor.way_ids == [7]
    assert calculation.corridor.lines == [[[40.0, 44.0], [41.0, 45.0]]]


def test_status_restores_speed_card_without_submitting_again() -> None:
    graph = Mock()
    graph.job.return_value = RoadJob(
        "existing", "1", "Region", "summer", [RoadChange(7, 1.2)], "running", 121, 360, "test"
    )
    graph.geometry.return_value = Mock(
        names=["R-1"], length_km=4, lines=[[[40.0, 44.0], [41.0, 45.0]]]
    )
    run = ChatRun(ChatContext(None, Season.SUMMER, NetworkMode.ROAD, "hansen"))
    RoadTools(graph).road_calculation_status(Mock(spec=RunContext, deps=run), "existing")
    assert len(run.pending) == 1
    assert run.pending[0].calculation is not None
    assert run.pending[0].calculation.job_ids == ["existing"]
    graph.submit.assert_not_called()


def test_missing_geometry_does_not_leave_a_started_job_without_a_card() -> None:
    graph = Mock()
    graph.geometry.side_effect = DataUnavailable("Geometry is missing")
    with pytest.raises(ModelRetry, match="Geometry is missing"):
        RoadTools(graph).recalculate_road_index(Mock(), "1", "summer", [RoadChange(7, 1.2)])
    graph.submit.assert_not_called()


def test_recent_calculations_recover_the_id_and_parameters_from_old_chat() -> None:
    graph = Mock()
    graph.recent.return_value = [
        RoadJob(
            "earlier", "1", "Region", "summer", [RoadChange(7, 1.2)], "completed", 360, 360, "test"
        )
    ]
    result = json.loads(RoadTools(graph).recent_road_calculations(Mock()))
    assert result[0]["id"] == "earlier"
    assert result[0]["scenario"] == "summer"
    assert result[0]["changes"] == [{"way_id": 7, "speed_factor": 1.2}]
    graph.submit.assert_not_called()
