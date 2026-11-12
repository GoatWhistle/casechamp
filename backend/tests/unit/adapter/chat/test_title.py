import asyncio
from types import SimpleNamespace
from typing import cast
from unittest.mock import MagicMock, Mock, patch

import pytest
from pydantic_ai import Agent, ModelRetry, RunContext
from pydantic_ai.capabilities import PrepareTools
from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart, ToolCallPart, ToolReturnPart
from pydantic_ai.models.function import AgentInfo, FunctionModel

from app.adapter.chat.artifacts import ChatRun
from app.adapter.chat.gateway import CodexResponsesGateway
from app.adapter.chat.title import name_chat
from app.adapter.chat.tool_visibility import analyst_tools
from app.domain.transport import NetworkMode, Season
from app.usecase.chat import ChatContext, ChatEvent, ChatMessage, ChatRequest
from app.usecase.chat_calculation_review import CalculationReview


def context() -> RunContext[ChatRun]:
    run = ChatRun(ChatContext(None, Season.SUMMER, NetworkMode.ROAD, "hansen"))
    return cast(RunContext[ChatRun], SimpleNamespace(deps=run))


def test_title_is_normalized_and_emitted_only_once() -> None:
    ctx = context()
    name_chat(ctx, "  «Закрытие  дорог\nВладимирской области».  ")
    name_chat(ctx, "Другая тема")
    assert ctx.deps.title == "Закрытие дорог Владимирской области"
    assert ctx.deps.pending == [ChatEvent("title", text=ctx.deps.title)]


@pytest.mark.parametrize("title", ["", "   ", "a" * 81])
def test_invalid_title_does_not_change_chat(title: str) -> None:
    ctx = context()
    with pytest.raises(ModelRetry):
        name_chat(ctx, title)
    assert ctx.deps.title is None
    assert not ctx.deps.pending


@pytest.mark.parametrize("mode", ["initial", "history", "analysis", "review", "disabled"])
def test_title_tool_is_only_available_for_the_initial_question(mode: str) -> None:
    agent = MagicMock()
    agent.run_stream_events.return_value.__aenter__.return_value.__aiter__.return_value = []
    gateway = CodexResponsesGateway.__new__(CodexResponsesGateway)
    gateway._tools = Mock()
    gateway._skills = Mock()
    gateway._skills.catalog.return_value = ""
    request = ChatRequest(
        "Question",
        (ChatMessage("user", "Original question"),) if mode == "history" else (),
        ChatContext(None, Season.SUMMER, NetworkMode.ROAD, "hansen"),
        analysis_id="analysis" if mode == "analysis" else None,
        calculation_review=CalculationReview(("job",), ()) if mode == "review" else None,
        title_requested=mode != "disabled",
    )

    async def collect() -> list[ChatEvent]:
        return [event async for event in gateway._run(request, Mock(), Mock())]

    with (
        patch("app.adapter.chat.gateway.Agent", return_value=agent),
        patch("app.adapter.chat.gateway.OpenAICodexModel"),
    ):
        assert asyncio.run(collect()) == [ChatEvent("done")]
    if mode == "initial":
        agent.tool.assert_called_once()
    else:
        agent.tool.assert_not_called()


def test_title_survives_tool_filter_and_is_hidden_after_naming() -> None:
    def respond(messages: list[ModelMessage], info: AgentInfo) -> ModelResponse:
        results = [
            part
            for message in messages
            for part in message.parts
            if isinstance(part, ToolReturnPart)
        ]
        names = [tool.name for tool in info.function_tools]
        if not results:
            assert names == ["name_chat"]
            return ModelResponse([ToolCallPart("name_chat", {"title": "Test topic"}, "title")])
        assert names == []
        return ModelResponse([TextPart("Answer")])

    agent: Agent[ChatRun, str] = Agent(
        FunctionModel(respond),
        deps_type=ChatRun,
        capabilities=[PrepareTools(analyst_tools)],
    )
    agent.tool(sequential=True, description="Name this conversation.")(name_chat)
    ctx = context()
    result = asyncio.run(agent.run("Question", deps=ctx.deps))
    assert result.output == "Answer"
    assert ctx.deps.pending == [ChatEvent("title", text="Test topic")]
