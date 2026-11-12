import json
from unittest.mock import Mock

from app.adapter.chat.artifacts import ChatRun
from app.adapter.chat.corridor_tools import CorridorTools
from app.domain.transport import NetworkMode, Season
from app.usecase.chat import ChatContext
from app.usecase.road_corridor import RoadCorridor, RoadRoute


def test_resolved_route_is_drawn_from_stored_geometry_in_the_same_reply() -> None:
    corridor = RoadCorridor(
        "route-id",
        "R-217",
        "Origin",
        "Destination",
        [123],
        59,
        0.1,
        0.2,
        [],
        [[[41.9, 45.0], [41.8, 44.6]]],
    )
    source = Mock(resolve_route=Mock(return_value=RoadRoute(corridor, 58 / 60)))
    ctx = Mock(deps=ChatRun(ChatContext(None, Season.SUMMER, NetworkMode.ROAD, "hansen")))
    reply = json.loads(CorridorTools(source).resolve_road_route(ctx, "Origin", "Destination"))
    assert reply["travel_hours"] == 58 / 60
    assert len(ctx.deps.pending) == 1
    command = ctx.deps.pending[0].map
    assert command is not None and command.action == "focus_road"
    assert command.road is not None and command.road.lines == corridor.lines
    assert "lines" not in reply and "way_ids" not in reply
