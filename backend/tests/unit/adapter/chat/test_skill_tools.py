import asyncio
from pathlib import Path
from unittest.mock import Mock

import pytest
from pydantic_ai import Agent, ModelRetry
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart, ToolCallPart, ToolReturnPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from app.adapter.chat.artifacts import ChatRun
from app.adapter.chat.skill_tools import SkillTools
from app.domain.transport import NetworkMode, Season
from app.usecase.chat import ChatContext


def test_catalog_does_not_inject_skill_bodies_and_loader_uses_requested_skill(tmp_path: Path) -> None:
    skill = tmp_path / "example"
    skill.mkdir()
    (skill / "SKILL.md").write_text(
        "---\nname: example\ndescription: Example task\n---\nDetailed guidance only on demand."
    )
    tools = SkillTools(tmp_path)
    assert tools.catalog() == "- example: Example task"
    assert "Detailed guidance" not in tools.catalog()
    assert tools.load_skill(Mock(), "example") == "Detailed guidance only on demand."
    with pytest.raises(ModelRetry, match="Unknown skill"):
        tools.load_skill(Mock(), "../example/SKILL.md")


def test_agent_can_load_domain_guidance_through_the_actual_tool_protocol() -> None:
    tools = SkillTools()
    returned = []

    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        assert "load_skill" in {tool.name for tool in info.function_tools}
        results = [
            part for message in messages for part in message.parts
            if isinstance(part, ToolReturnPart)
        ]
        if not results:
            return ModelResponse([
                ToolCallPart("load_skill", {"name": "economic-assessment"}, "skill-call")
            ])
        returned.append(results[-1].content)
        return ModelResponse([TextPart("Guidance loaded")])

    agent: Agent[ChatRun, str] = Agent(
        FunctionModel(respond), instructions=tools.catalog(), deps_type=ChatRun,
    )
    tools.register(agent)
    run = ChatRun(ChatContext(None, Season.SUMMER, NetworkMode.ROAD, "hansen"))
    result = asyncio.run(agent.run("Assess transport benefits", deps=run))
    assert result.output == "Guidance loaded"
    assert returned == [tools.load_skill(Mock(), "economic-assessment")]
    assert not run.pending


def test_empty_skill_package_fails_clearly(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="No bundled analyst skills"):
        SkillTools(tmp_path)
