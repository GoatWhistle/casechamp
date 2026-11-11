import asyncio
from types import SimpleNamespace
from typing import cast
from unittest.mock import MagicMock, Mock, patch

import pytest
from pydantic_ai import ModelRetry, RunContext

from app.adapter.chat.artifacts import ChatRun
from app.adapter.chat.gateway import CodexResponsesGateway
from app.adapter.chat.title import name_chat
from app.domain.transport import NetworkMode, Season
from app.usecase.chat import ChatContext, ChatEvent, ChatMessage, ChatRequest


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


@pytest.mark.parametrize("with_history", [False, True])
def test_title_tool_is_only_available_for_the_initial_question(with_history: bool) -> None:
    agent = MagicMock()
    agent.run_stream_events.return_value.__aenter__.return_value.__aiter__.return_value = []
    gateway = CodexResponsesGateway.__new__(CodexResponsesGateway)
    gateway._tools = Mock()
    request = ChatRequest(
        "Show sources",
        (ChatMessage("user", "Original question"),) if with_history else (),
        ChatContext(None, Season.SUMMER, NetworkMode.ROAD, "hansen"),
        title_requested=True,
    )

    async def collect() -> list[ChatEvent]:
        return [event async for event in gateway._run(request, Mock())]

    with (
        patch("app.adapter.chat.gateway.Agent", return_value=agent),
        patch("app.adapter.chat.gateway.OpenAICodexModel"),
    ):
        assert asyncio.run(collect()) == [ChatEvent("done")]
    if with_history:
        agent.tool.assert_not_called()
    else:
        agent.tool.assert_called_once()
