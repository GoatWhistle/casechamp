import asyncio
import json
from unittest.mock import Mock

from pydantic_ai import Agent
from pydantic_ai.capabilities import PrepareTools
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart, ToolCallPart, ToolReturnPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from app.adapter.chat.artifacts import ChatRun
from app.adapter.chat.calculation_tools import CalculationTools
from app.adapter.chat.skill_tools import SkillTools
from app.adapter.chat.tool_visibility import analyst_tools
from app.adapter.chat.tools import AtlasTools
from app.domain.transport import NetworkMode, Season
from app.usecase.chat import ChatContext
from app.usecase.road_corridor import CorridorRegion, RoadCorridor, RoadRoute
from app.usecase.road_graph import RoadJob


def test_fresh_agent_sees_only_skill_loading_and_atlas_query() -> None:
    def inspect(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        names = sorted(tool.name for tool in info.function_tools)
        size = len(
            json.dumps(
                [
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.parameters_json_schema,
                    }
                    for tool in info.function_tools
                ],
                ensure_ascii=False,
            )
        )
        print("tool_count", len(names), "schema_characters", size)
        return ModelResponse([TextPart(json.dumps(names))])

    agent: Agent[ChatRun, str] = Agent(
        FunctionModel(inspect), deps_type=ChatRun, capabilities=[PrepareTools(analyst_tools)]
    )
    SkillTools().register(agent)
    AtlasTools(
        Mock(), Mock(), Mock(), Mock(), Mock(), CalculationTools(Mock(), Mock(), Mock(), Mock())
    ).register(agent)
    run = ChatRun(ChatContext(None, Season.SUMMER, NetworkMode.ROAD, "hansen"))
    names = json.loads(asyncio.run(agent.run("Inspect", deps=run)).output)
    assert names == ["load_skill", "query_atlas"]


def test_loading_skill_exposes_unified_search_and_scenario_on_the_next_step() -> None:
    corridor = RoadCorridor(
        "selection",
        "Road",
        "A",
        "B",
        [7],
        1,
        0,
        0,
        [CorridorRegion("region", "Region")],
        [[[40.0, 44.0], [41.0, 45.0]]],
    )
    corridors = Mock()
    corridors.resolve_route.return_value = RoadRoute(corridor, 1)
    corridors.get.return_value = corridor
    corridors.combined.return_value = corridor
    corridors.close.return_value = [
        RoadJob("job", "region", "Region", "road", [], "queued", 0, 360, "v")
    ]
    seen = []

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        names = {tool.name for tool in info.function_tools}
        seen.append(names)
        returned = [p for m in messages for p in m.parts if isinstance(p, ToolReturnPart)]
        if not returned:
            return ModelResponse([ToolCallPart("load_skill", {"name": "road-scenarios"})])
        if len(returned) == 1:
            return ModelResponse(
                [
                    ToolCallPart(
                        "find_transport",
                        {
                            "request": {
                                "kind": "road",
                                "origin": "Town A",
                                "destination": "Town B",
                            }
                        },
                    )
                ]
            )
        if len(returned) == 2:
            result = json.loads(str(returned[-1].content))
            return ModelResponse(
                [
                    ToolCallPart(
                        "calculate_scenario",
                        {
                            "request": {
                                "kind": "close_selection",
                                "selection_ids": [result["id"]],
                                "assessment": "hansen",
                            }
                        },
                    )
                ]
            )
        return ModelResponse([TextPart("Submitted")])

    agent: Agent[ChatRun, str] = Agent(
        FunctionModel(respond),
        deps_type=ChatRun,
        capabilities=[PrepareTools(analyst_tools)],
    )
    SkillTools().register(agent)
    AtlasTools(
        Mock(), Mock(), Mock(), Mock(), Mock(), CalculationTools(Mock(), Mock(), Mock(), corridors)
    ).register(agent)
    run = ChatRun(ChatContext(None, Season.SUMMER, NetworkMode.ROAD, "hansen"))
    assert asyncio.run(agent.run("Close the road between A and B", deps=run)).output == "Submitted"
    assert seen[0] == {"load_skill", "query_atlas"}
    assert seen[1] == {
        "load_skill",
        "query_atlas",
        "find_transport",
        "calculate_scenario",
        "manage_calculation",
    }
    corridors.resolve_route.assert_called_once_with("Town A", "Town B")
    corridors.close.assert_called_once_with(["selection"])
    assert run.pending[0].calculation is not None
    assert run.pending[0].calculation.job_ids == ["job"]


def test_all_skills_still_expose_only_six_tools_and_do_not_leak_to_another_run() -> None:
    inventories = []

    def inspect(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        inventories.append({tool.name for tool in info.function_tools})
        size = len(
            json.dumps(
                [
                    {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.parameters_json_schema,
                    }
                    for t in info.function_tools
                ],
                ensure_ascii=False,
            )
        )
        print("tool_count", len(info.function_tools), "schema_characters", size)
        return ModelResponse([TextPart("Inspected")])

    agent: Agent[ChatRun, str] = Agent(
        FunctionModel(inspect),
        deps_type=ChatRun,
        capabilities=[PrepareTools(analyst_tools)],
    )
    skills = SkillTools()
    skills.register(agent)
    AtlasTools(
        Mock(), Mock(), Mock(), Mock(), Mock(), CalculationTools(Mock(), Mock(), Mock(), Mock())
    ).register(agent)
    first = ChatRun(ChatContext(None, Season.SUMMER, NetworkMode.ROAD, "hansen"))
    first.loaded_skills.update(skills.skills)
    second = ChatRun(first.context)
    asyncio.run(agent.run("Inspect", deps=first))
    asyncio.run(agent.run("Inspect", deps=second))
    assert inventories[0] == {
        "load_skill",
        "query_atlas",
        "find_transport",
        "calculate_scenario",
        "manage_calculation",
        "present_atlas",
    }
    assert inventories[1] == {"load_skill", "query_atlas"}
