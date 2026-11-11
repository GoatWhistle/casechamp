import json
from unittest.mock import Mock

import pytest

from app.adapter.chat.artifacts import ChatRun
from app.adapter.chat.bridge_tools import BridgeTools
from app.adapter.road_corridor.resolver import CorridorResolver
from app.domain.bridge_groups import BridgePart, bridge_groups, distance_to_line_km
from app.domain.transport import NetworkMode, Season
from app.usecase.chat import ChatContext
from app.usecase.road_corridor import RoadCorridors
from app.usecase.road_graph import RoadJob


def part(way: int, source: int, target: int, lat: float, ref: str = "R-1") -> BridgePart:
    return BridgePart(
        way, "Bridge", ref, "primary", 1.0, source, target, [[40.0, lat], [40.02, lat]]
    )


def test_bridge_grouping_includes_parallel_decks_and_excludes_nearby_unrelated_bridge() -> None:
    pieces = [part(1, 10, 11, 50), part(2, 20, 21, 50.0001), part(3, 30, 31, 50.0002, "R-2")]
    groups = bridge_groups(pieces)
    assert [{p.way_id for p in group} for group in groups] == [{1, 2}, {3}]


def test_connected_fragments_group_but_distant_bridge_on_same_road_stays_separate() -> None:
    pieces = [part(1, 10, 11, 50), part(2, 11, 12, 50.01), part(3, 30, 31, 50.1)]
    assert [{p.way_id for p in group} for group in bridge_groups(pieces)] == [{1, 2}, {3}]


def test_distance_uses_bridge_span_instead_of_only_endpoints() -> None:
    assert distance_to_line_km([40.01, 50.0], [[40.0, 50.0], [40.02, 50.0]]) == pytest.approx(0)
    assert distance_to_line_km([40.0, 50.001], [[40.0, 50.0], [40.02, 50.0]]) == pytest.approx(
        0.111195
    )


def test_search_and_combined_closure_emit_one_job_with_both_decks_and_no_other_roads() -> None:
    roads = Mock()
    rows = [
        (1, "Direct bridge", "R-1", "primary", 1.0, 10, 11, [[40.0, 50.0], [40.02, 50.0]]),
        (2, "Bypass", "R-2", "trunk", 2.0, 20, 21, [[40.0, 50.01], [40.02, 50.01]]),
        (3, "Bypass", "R-2", "trunk", 2.0, 30, 31, [[40.0, 50.0101], [40.02, 50.0101]]),
        (4, "Unrelated bridge", "R-3", "primary", 1.0, 40, 41, [[40.0, 50.02], [40.02, 50.02]]),
    ]
    roads.data.read.side_effect = lambda query, params: {
        "corridor_places": [("1", "Town", "Region", 40.0, 50.0)],
        "bridge_parts": rows,
        "region_codes": [("region", "Region")],
        "bridge_lengths": [(1, 1.0), (2, 2.0), (3, 2.0)],
    }[query]
    roads.submit.return_value = RoadJob(
        "job", "region", "Region", "road", [], "queued", 0, 360, "test"
    )
    tools = BridgeTools(RoadCorridors(CorridorResolver(roads)))
    ctx = Mock()
    ctx.deps = ChatRun(ChatContext(None, Season.SUMMER, NetworkMode.ROAD, "hansen"))
    candidates = json.loads(tools.find_road_bridges(ctx, "Town"))["candidates"]
    selected = [c["bridge_id"] for c in candidates if c["name"] != "Unrelated bridge"]
    result = json.loads(tools.close_road_bridges(ctx, selected))
    assert result["status"] == "submitted"
    assert result["way_ids"] == [1, 2, 3]
    roads.submit.assert_called_once()
    changes = roads.submit.call_args.args[3]
    assert [(change.way_id, change.speed_factor) for change in changes] == [(1, 0), (2, 0), (3, 0)]
    event = ctx.deps.pending[0]
    assert event.calculation.job_ids == ["job"]
    assert len(event.calculation.corridor.lines) == 3
    assert event.calculation.corridor.length_km == 5.0


@pytest.mark.parametrize("ids", [[], ["unknown"], ["duplicate", "duplicate"]])
def test_invalid_selection_never_starts_a_calculation(ids: list[str]) -> None:
    roads = Mock()
    tools = BridgeTools(RoadCorridors(CorridorResolver(roads)))
    result = json.loads(tools.close_road_bridges(Mock(), ids))
    assert result["status"] == "unresolved"
    roads.submit.assert_not_called()


def test_ambiguous_settlement_returns_choices_without_a_partial_bridge_selection() -> None:
    roads = Mock()
    roads.data.read.return_value = [("1", "Town", "Region A"), ("2", "Town", "Region B")]
    tools = BridgeTools(RoadCorridors(CorridorResolver(roads)))
    result = json.loads(tools.find_road_bridges(Mock(), "Town"))
    assert result["status"] == "unresolved"
    assert "Region A" in result["message"]
    assert "Region B" in result["message"]
    roads.data.read.assert_called_once()
