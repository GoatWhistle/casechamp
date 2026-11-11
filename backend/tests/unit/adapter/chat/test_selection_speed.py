import json
from unittest.mock import Mock

import pytest
from pydantic import TypeAdapter

from app.adapter.chat.artifacts import ChatRun
from app.adapter.chat.network_scenarios import NetworkScenarios
from app.adapter.chat.road_tools import RoadTools
from app.adapter.chat.scenario_requests import TransportScenario
from app.adapter.road_corridor.resolver import CorridorResolver
from app.domain.errors import InvalidQuery
from app.domain.transport import NetworkMode, Season
from app.usecase.chat import ChatContext
from app.usecase.road_corridor import CorridorRegion, RoadCorridor, RoadCorridors
from app.usecase.road_graph import RoadJob


def setup_scenario() -> tuple[Mock, RoadCorridors]:
    roads = Mock()
    roads.submit.side_effect = lambda rid, name, scenario, changes, **kw: RoadJob(
        rid, rid, name, scenario, changes, "queued", 0, 360, "test"
    )
    resolver = CorridorResolver(roads)
    for key, ways in [("m10", list(range(1, 3001))), ("m11", list(range(2001, 5001)))]:
        resolver.resolved[key] = RoadCorridor(
            key,
            key,
            "Moscow",
            "Petersburg",
            ways,
            700,
            0,
            0,
            [CorridorRegion("1", "First"), CorridorRegion("2", "Second")],
            [],
        )
    return roads, RoadCorridors(resolver)


def test_joint_speed_resolves_large_selection_internally_on_open_baseline() -> None:
    roads, corridors = setup_scenario()
    request = TypeAdapter(TransportScenario).validate_python(
        {
            "kind": "edit_selection",
            "selection_ids": ["m10", "m11"],
            "speed_factor": 1.2,
        }
    )
    ctx = Mock(deps=ChatRun(ChatContext(None, Season.SUMMER, NetworkMode.ROAD, "hansen")))
    reply = NetworkScenarios(None, corridors, None).calculate_scenario(ctx, request)
    assert len(reply) < 1000
    assert len(json.loads(reply)) == 2
    assert roads.submit.call_count == 2
    for call in roads.submit.call_args_list:
        assert call.args[2] == "road"
        changes = call.args[3]
        assert len(changes) == 5000
        assert {c.speed_factor for c in changes} == {1.2}
        assert call.kwargs == {"queue": True}
    assert len(ctx.deps.pending) == 1
    assert ctx.deps.pending[0].calculation.job_ids == ["1", "2"]
    assert len(ctx.deps.pending[0].calculation.changes) == 5000


@pytest.mark.parametrize(
    "ids,factor",
    [([], 1.2), (["m10", "m10"], 1.2), (["m10"], -1), (["m10"], float("nan")), (["m10"], 4)],
)
def test_invalid_edit_never_submits(ids: list[str], factor: float) -> None:
    roads, corridors = setup_scenario()
    with pytest.raises(InvalidQuery):
        corridors.edit(ids, factor)
    roads.submit.assert_not_called()


def test_status_and_history_do_not_expand_large_way_lists() -> None:
    roads, corridors = setup_scenario()
    job = corridors.edit(["m10", "m11"], 1.2)[0]
    roads.job.return_value = job
    roads.recent.return_value = [job]
    roads.geometry.return_value = Mock(names=["M10", "M11"], length_km=700, lines=[])
    ctx = Mock(deps=ChatRun(ChatContext(None, Season.SUMMER, NetworkMode.ROAD, "hansen")))
    tools = RoadTools(roads)
    status = json.loads(tools.road_calculation_status(ctx, job.id))
    recent = json.loads(tools.recent_road_calculations(ctx))[0]
    for payload in [status, recent]:
        assert payload["changed_ways"] == 5000
        assert payload["changes_truncated"] is True
        assert len(payload["changes"]) == 20
    assert len(job.changes) == 5000
