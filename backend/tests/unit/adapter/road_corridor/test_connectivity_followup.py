import asyncio
import json
from pathlib import Path

from pydantic_ai import Agent
from pydantic_ai.capabilities import PrepareTools
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart, ToolCallPart, ToolReturnPart
from pydantic_ai.models.function import AgentInfo, FunctionModel
from tests.unit.adapter.road_corridor.test_group_connectivity import network

from app.adapter.chat.artifacts import ChatRun
from app.adapter.chat.network_jobs import NetworkJobs
from app.adapter.chat.network_scenarios import NetworkScenarios
from app.adapter.chat.skill_tools import SkillTools
from app.adapter.chat.tool_visibility import analyst_tools
from app.adapter.road_corridor.resolver import CorridorResolver
from app.domain.transport import NetworkMode, Season
from app.usecase.chat import ChatContext
from app.usecase.road_corridor import RoadCorridors


def test_two_agent_turns_compute_then_read_saved_economics_without_resubmitting(
    tmp_path: Path,
) -> None:
    corridors, roads = network()
    roads.data.root = tmp_path
    reference: list[str] = []
    stage = [0]

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        returned = [
            part
            for message in messages
            for part in message.parts
            if isinstance(part, ToolReturnPart)
        ]
        if not returned:
            return ModelResponse(
                [
                    ToolCallPart(
                        "load_skill",
                        {
                            "name": "settlement-connectivity"
                            if stage[0] == 0
                            else "economic-assessment"
                        },
                    )
                ]
            )
        if len(returned) == 1:
            names = {tool.name for tool in info.function_tools}
            if stage[0] == 0:
                assert "calculate_scenario" in names
                return ModelResponse(
                    [
                        ToolCallPart(
                            "calculate_scenario",
                            {
                                "request": {
                                    "kind": "connectivity",
                                    "places": ["Village A", "Village C"],
                                    "selection_ids": ["fast"],
                                    "traffic": {},
                                }
                            },
                        )
                    ]
                )
            assert "manage_calculation" in names
            return ModelResponse(
                [
                    ToolCallPart(
                        "manage_calculation",
                        {
                            "request": {
                                "kind": "connectivity_economics",
                                "calculation_id": reference[0],
                                "value_of_pcu_hour_rub": 500,
                            }
                        },
                    )
                ]
            )
        result = json.loads(str(returned[-1].content))
        if stage[0] == 0:
            reference.append(result["calculation_id"])
            assert result["pairs"][0]["traffic"]["displaced_flow_pcu_h"] == 1800
        else:
            assert result["calculation_id"] == reference[0]
            assert result["pairs"][0]["time_cost_rub"] > 0
        return ModelResponse([TextPart("Verified saved calculation")])

    def agent(restored: RoadCorridors) -> Agent[ChatRun, str]:
        instance: Agent[ChatRun, str] = Agent(
            FunctionModel(respond), deps_type=ChatRun, capabilities=[PrepareTools(analyst_tools)]
        )
        SkillTools().register(instance)
        NetworkScenarios(None, restored, None).register(instance)
        NetworkJobs(None, None, restored).register(instance)
        return instance

    context = ChatContext(None, Season.SUMMER, NetworkMode.ROAD, "hansen")
    first = ChatRun(context)
    asyncio.run(agent(corridors).run("Model closure under average traffic", deps=first))
    stage[0] = 1
    assert first.pending[0].table is not None
    assert first.pending[0].table.rows[0]["calculation_id"] == reference[0]
    asyncio.run(
        agent(RoadCorridors(CorridorResolver(roads))).run(
            "And economically? Saved calculation: " + reference[0],
            deps=ChatRun(context),
        )
    )
    assert len(list((tmp_path / "connectivity-results").glob("*.json"))) == 1
