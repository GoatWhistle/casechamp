import asyncio
import json
from pathlib import Path
from tempfile import mkdtemp
from typing import Any
from unittest.mock import Mock

import numpy as np
import pytest
from pydantic_ai import Agent
from pydantic_ai.capabilities import PrepareTools
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart, ToolCallPart, ToolReturnPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from app.adapter.chat.artifacts import ChatRun
from app.adapter.chat.network_scenarios import NetworkScenarios
from app.adapter.chat.scenario_requests import ConnectivityScenario
from app.adapter.chat.skill_tools import SkillTools
from app.adapter.chat.tool_visibility import analyst_tools
from app.adapter.road_corridor.resolver import CorridorResolver
from app.adapter.road_graph.routing import minimum_csr
from app.domain.errors import InvalidQuery
from app.domain.transport import NetworkMode, Season
from app.usecase.chat import ChatContext
from app.usecase.road_corridor import RoadCorridor, RoadCorridors


def network() -> tuple[RoadCorridors, Mock]:
    roads = Mock()
    roads.data.root = Path(mkdtemp(prefix="connectivity-test-"))
    edges = {
        "src": np.array([0, 0, 1, 0, 2]),
        "dst": np.array([1, 1, 2, 2, 3]),
        "h": np.array([1.0, 2.0, 1.0, 4.0, 2.0]),
        "way_idx": np.array([0, 1, 2, 3, 4]),
    }
    roads.data.edges = edges
    roads.data.cost_profiles.side_effect = lambda ids: {
        way - 101: {"highway": "trunk", "lanes_total": 4 if way == 101 else 2}
        for way in ids
    }
    roads.data.nodes = {"lat": np.zeros(4)}
    roads.data.version = "snapshot-test"
    roads.data.allowed_edges.return_value = np.ones(5, dtype=bool)
    roads.data.indices_for.side_effect = lambda ids: {way: way - 101 for way in ids}
    roads.delta.base.graph = minimum_csr(edges["src"], edges["dst"], edges["h"], 4)

    def read(query: str, params: dict[str, Any]) -> list[tuple[Any, ...]]:
        if query == "corridor_places":
            name = params["query"]
            if name == "Ambiguous":
                return [("a", "Village A", "R1"), ("b", "Village A", "R2")]
            if name == "Alias":
                name = "Village A"
            index = "ABCDE".index(name[-1])
            return [(str(index), name, "Region")]
        if query == "route_points":
            return [(str(i), i, 0.0) for i in range(4)]
        if query == "route_edges":
            return [(int(a), int(b), i, float(h))
                    for i, (a, b, h) in enumerate(zip(edges["src"], edges["dst"], edges["h"], strict=True))
                    if a in params["ids"] and b in params["ids"]]
        if query == "references_by_ids":
            return [(i, i + 101, "Road", "R1", 1.0) for i in params["ids"]]
        raise AssertionError(query)

    roads.data.read.side_effect = read
    resolver = CorridorResolver(roads)
    for key, ways in {"fast": [101], "parallel": [102], "bridge": [105]}.items():
        resolver.resolved[key] = RoadCorridor(key, key, "A", "B", ways, 1, 0, 0, [], [])
    return RoadCorridors(resolver), roads


@pytest.mark.parametrize(("count", "pairs"), [(2, 1), (3, 3), (4, 6)])
def test_selected_group_counts_pairs_without_self_contributions(count: int, pairs: int) -> None:
    corridors, _ = network()
    result = corridors.connectivity(["Village " + c for c in "ABCD"[:count]])
    assert len(result.pairs) == result.reachable_before == pairs
    assert result.score_before == result.score_after
    assert result.delta == 0
    assert all(pair.origin.id != pair.destination.id for pair in result.pairs)


def test_closure_recomputes_detours_and_preserves_parallel_edges_and_baseline() -> None:
    corridors, roads = network()
    original = roads.data.edges["h"].copy()
    result = corridors.connectivity(["Village A", "Village B"], selection_ids=["fast"])
    assert result.pairs[0].before.hours == 1
    assert result.pairs[0].after.hours == 2
    assert result.score_after == pytest.approx(50)
    assert result.delta is not None and result.delta < 0
    joint = corridors.connectivity(
        ["Village A", "Village B"],
        selection_ids=["fast", "parallel"],
    )
    assert joint.pairs[0].after.hours == 5
    np.testing.assert_array_equal(roads.data.edges["h"], original)
    roads.submit.assert_not_called()


def test_bridge_closure_keeps_disconnected_pairs_in_fixed_denominator() -> None:
    corridors, _ = network()
    result = corridors.connectivity(
        ["Village " + c for c in "ABCD"],
        selection_ids=["bridge"],
    )
    assert result.reachable_before == 6
    assert result.reachable_after == 3
    assert result.disconnected_pairs == 3
    assert result.unbound_pairs == 0
    assert result.score_after == pytest.approx((2 * 100 * 2**-0.5 + 50) / 6)
    disconnected = [p for p in result.pairs if p.after.status == "unreachable"]
    assert all(p.after.hours is None and p.score_after == 0 for p in disconnected)


def test_center_mode_only_evaluates_origins_to_selected_center() -> None:
    corridors, _ = network()
    result = corridors.connectivity(
        ["Village " + c for c in "ABCD"],
        "to_center",
        "Village D",
        ["bridge"],
    )
    assert len(result.pairs) == 3
    assert result.center_id == "3"
    assert all(p.destination.name == "Village D" for p in result.pairs)
    assert result.score_after == 0
    assert result.disconnected_pairs == 3


def test_missing_attachment_is_unknown_and_blocks_group_score() -> None:
    corridors, _ = network()
    result = corridors.connectivity(["Village A", "Village B", "Village E"])
    assert result.score_before is None and result.score_after is None
    assert result.unbound_pairs == 2 and result.reachable_before == 1
    assert result.disconnected_pairs == 0
    assert result.pairs[1].score_before is None


@pytest.mark.parametrize(
    ("places", "mode", "center", "message"),
    [
        (["Village A"], "all_pairs", None, "2 to 12"),
        (["Village A", "Village A"], "all_pairs", None, "distinct"),
        (["Village A", "Alias"], "all_pairs", None, "same settlement"),
        (["Village A", "Ambiguous"], "all_pairs", None, "ambiguous"),
        (["Village A", "Village B"], "to_center", None, "center"),
        (["Village A", "Village B"], "all_pairs", "Village A", "center"),
    ],
)
def test_invalid_group_does_not_produce_a_score(
    places: list[str],
    mode: Any,
    center: str | None,
    message: str,
) -> None:
    corridors, _ = network()
    with pytest.raises(InvalidQuery, match=message):
        corridors.connectivity(places, mode, center)


def test_chat_returns_computed_summary_and_pairs_for_joint_closure() -> None:
    corridors, _ = network()
    ctx = Mock(deps=ChatRun(ChatContext(None, Season.SUMMER, NetworkMode.ROAD, "hansen")))
    result = json.loads(
        NetworkScenarios(None, corridors, None).calculate_scenario(
            ctx,
            ConnectivityScenario(
                "connectivity",
                ["Village A", "Village D"],
                selection_ids=["bridge"],
            ),
        )
    )
    assert result["score_after"] == 0
    assert result["disconnected_pairs"] == 1
    assert [event.table.title for event in ctx.deps.pending] == [
        "connectivity_summary",
        "connectivity",
    ]
    assert ctx.deps.pending[1].table.rows[0]["status_after"] == "unreachable"
    assert ctx.deps.pending[1].table.rows[0]["hours_after"] is None


def test_skill_and_typed_tool_execute_selected_group_closure_through_agent_protocol() -> None:
    corridors, _ = network()

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        returned = [p for m in messages for p in m.parts if isinstance(p, ToolReturnPart)]
        if not returned:
            return ModelResponse(
                [
                    ToolCallPart("load_skill", {"name": "settlement-connectivity"}),
                ]
            )
        if len(returned) == 1:
            assert "calculate_scenario" in {tool.name for tool in info.function_tools}
            return ModelResponse(
                [
                    ToolCallPart(
                        "calculate_scenario",
                        {
                            "request": {
                                "kind": "connectivity",
                                "places": ["Village A", "Village D"],
                                "mode": "to_center",
                                "center": "Village D",
                                "selection_ids": ["bridge"],
                            }
                        },
                    )
                ]
            )
        result = json.loads(str(returned[-1].content))
        assert result["score_after"] == 0 and result["disconnected_pairs"] == 1
        return ModelResponse([TextPart("Verified")])

    agent: Agent[ChatRun, str] = Agent(
        FunctionModel(respond),
        deps_type=ChatRun,
        capabilities=[PrepareTools(analyst_tools)],
    )
    SkillTools().register(agent)
    NetworkScenarios(None, corridors, None).register(agent)
    run = ChatRun(ChatContext(None, Season.SUMMER, NetworkMode.ROAD, "hansen"))
    assert (
        asyncio.run(agent.run("Compare center access after bridge closure", deps=run)).output
        == "Verified"
    )
    assert len(run.tables) == 2
