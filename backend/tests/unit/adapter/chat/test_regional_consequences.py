import asyncio
import json
from unittest.mock import Mock

import pytest
from pydantic_ai import Agent
from pydantic_ai.capabilities import PrepareTools
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart, ToolCallPart, ToolReturnPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from app.adapter.chat.artifacts import ChatRun
from app.adapter.chat.skill_tools import SkillTools
from app.adapter.chat.stress_tools import StressTools
from app.adapter.chat.tool_visibility import analyst_tools
from app.adapter.road_graph.search_cache import SearchCache
from app.adapter.road_stress.jobs import StressJobs
from app.domain.errors import InvalidQuery
from app.domain.transport import NetworkMode, Season
from app.usecase.chat import ChatContext
from app.usecase.road_consequences import (
    ConnectionConsequence,
    DelayExposure,
    NearbyAccessChange,
    RegionalConsequences,
)
from app.usecase.road_stress import StressJob, StressRegion, StressSummary, StressTotals


def report() -> RegionalConsequences:
    return RegionalConsequences(
        "Region",
        2,
        2,
        150,
        [DelayExposure(60, 2, 300)],
        NearbyAccessChange(2, 3, 1, 2, 60, 112.5, 52.5, 2, 2, 150),
        [],
        [
            ConnectionConsequence("a", "Village A", 100, "City", 60, 150, 90),
            ConnectionConsequence("b", "Village B", 50, "City", 90, None, None),
        ],
    )


def test_agent_receives_region_prediction_and_named_before_after_connections() -> None:
    engine = Mock()
    engine.geometry.return_value.names = ["М-10"]
    engine.get.return_value = StressJob("saved", "v", [1], status="completed")
    engine.summary.return_value = StressSummary(
        "saved",
        "v",
        "completed",
        "completed",
        1,
        None,
        "Region",
        StressTotals(3, 350, 1, 50, 120, 1),
        1000,
        10,
        2,
        180,
        180,
        report(),
    )
    engine.impacts.return_value = []

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        returned = [p for m in messages for p in m.parts if isinstance(p, ToolReturnPart)]
        if not returned:
            return ModelResponse([ToolCallPart("load_skill", {"name": "road-scenarios"})])
        if len(returned) == 1:
            assert "inspect_road_stress_test" in {t.name for t in info.function_tools}
            return ModelResponse(
                [
                    ToolCallPart(
                        "inspect_road_stress_test",
                        {
                            "job_id": "saved",
                            "region": "49000000",
                        },
                    )
                ]
            )
        payload = json.loads(str(returned[-1].content))
        consequences = payload["summary"]["consequences"]
        assert consequences["nearby_access"]["mean_before_minutes"] == 60
        assert consequences["nearby_access"]["mean_after_minutes"] == 112.5
        assert consequences["nearby_access"]["comparable_connections"] == 2
        assert consequences["examples"][1]["after_minutes"] is None
        assert consequences["delay_exposure"][0]["residents"] == 300
        return ModelResponse([TextPart("Verified regional consequences")])

    agent: Agent[ChatRun, str] = Agent(
        FunctionModel(respond), deps_type=ChatRun, capabilities=[PrepareTools(analyst_tools)]
    )
    SkillTools().register(agent)
    StressTools(engine, None).register(agent)
    result = asyncio.run(
        agent.run(
            "What changes in this region?",
            deps=ChatRun(
                ChatContext(
                    "49000000", Season.SUMMER, NetworkMode.ROAD, "hansen", stress_job_id="saved"
                ),
            ),
        )
    )
    assert result.output == "Verified regional consequences"
    engine.summary.assert_called_once_with("saved", "49000000")
    engine.impacts.assert_called_once_with("saved", "Region", 0, 5)
    engine.submit.assert_not_called()


def test_completed_consequence_cache_is_partitioned_by_job_and_region() -> None:
    engine = Mock()
    engine.geometry.return_value.names = ["М-10"]
    engine.consequence_cache = SearchCache(32)
    engine.store.consequences.return_value = report()
    for _ in range(2):
        assert StressJobs.consequences(engine, "saved", "Region") == report()
    engine.store.consequences.assert_called_once_with("saved", "Region")
    StressJobs.consequences(engine, "other", "Region")
    StressJobs.consequences(engine, "saved", "Another region")
    assert engine.store.consequences.call_count == 3


def test_summary_resolves_region_id_and_rejects_unknown_names() -> None:
    engine = Mock()
    engine.geometry.return_value.names = ["М-10"]
    engine.get.return_value = StressJob(
        "saved", "v", [1], status="completed", regions=[StressRegion("Region", 3, 350, 50)]
    )
    engine.roads.data.region_name.return_value = "Region"
    engine.roads.data.read.return_value = []
    engine.store.totals.return_value = StressTotals(3, 350, 1, 50, 120, 1)
    engine.consequences.return_value = report()
    summary = StressJobs.summary(engine, "saved", "49000000")
    assert summary.region == "Region"
    engine.consequences.assert_called_once_with("saved", "Region")
    with pytest.raises(InvalidQuery, match="Unknown region"):
        StressJobs.summary(engine, "saved", "Typo")
    engine.get.return_value = StressJob("pending", "v", [1])
    assert StressJobs.summary(engine, "pending", "").consequences is None
