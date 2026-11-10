import json
from unittest.mock import Mock

from pydantic_ai import RunContext

from app.adapter.chat.artifacts import ChatRun
from app.adapter.chat.corridor_tools import CorridorTools
from app.adapter.road_corridor.resolver import CorridorResolver
from app.domain.errors import InvalidQuery
from app.domain.transport import NetworkMode, Season
from app.usecase.chat import ChatContext
from app.usecase.road_corridor import CorridorRegion, RoadCorridor, RoadCorridors
from app.usecase.road_graph import RoadJob


def test_closure_emits_geometry_and_both_jobs_without_waiting_for_results() -> None:
    corridor = RoadCorridor(
        "corridor", "R-1", "A", "B", [7], 4, 0, 0,
        [CorridorRegion("1", "First"), CorridorRegion("2", "Second")],
        [[[40.0, 44.0], [41.0, 45.0]]],
    )
    engine = Mock()
    engine.get.return_value = corridor
    engine.close.return_value = [
        RoadJob(str(i), str(i), name, "road", [], "queued", 0, 360, "test")
        for i, name in [(1, "First"), (2, "Second")]
    ]
    run = ChatRun(ChatContext(None, Season.SUMMER, NetworkMode.ROAD, "hansen"))
    context = Mock(spec=RunContext)
    context.deps = run
    pending = run.pending
    tools = CorridorTools(RoadCorridors(engine))
    tools.close_road_corridor(context, "corridor")
    assert len(pending) == 1
    event = pending[0]
    assert event.type == "calculation"
    assert event.calculation is not None
    assert event.calculation.corridor.lines == corridor.lines
    assert event.calculation.job_ids == ["1", "2"]
    engine.close.assert_called_once_with("corridor")


def test_ambiguous_settlement_returns_actionable_result_without_exhausting_retries() -> None:
    engine = Mock()
    engine.resolve.side_effect = InvalidQuery("Settlement is ambiguous: Энгельс")
    context = Mock(spec=RunContext)
    result = json.loads(CorridorTools(RoadCorridors(engine)).resolve_road_corridor(
        context, "Р-228", "Саратов", "Энгельс"
    ))
    assert result["status"] == "unresolved"
    assert result["code"] == "validation_error"
    assert "Энгельс" in result["message"]
    engine.close.assert_not_called()


def test_empty_reference_alias_does_not_hide_settlement_choices() -> None:
    roads = Mock()
    roads.data.read.side_effect = [
        [("",), (None,), ("Р-228",)],
        [],
        [("1", "г. Саратов", "Саратовская область", 46., 51.)],
        [("2", "посёлок Энгельс", "Оренбургская область", 46., 51.),
         ("3", "г. Энгельс", "Саратовская область", 46., 51.)],
    ]
    tools = CorridorTools(RoadCorridors(CorridorResolver(roads)))
    result = json.loads(tools.resolve_road_corridor(Mock(), "Р-228", "Саратов", "Энгельс"))
    assert result["status"] == "unresolved"
    assert "Оренбургская область" in result["message"]
    assert "Саратовская область" in result["message"]
