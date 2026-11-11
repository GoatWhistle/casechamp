from types import SimpleNamespace
from typing import cast

import pytest
from pydantic_ai import ModelRetry, RunContext

from app.adapter.chat.artifacts import ChatRun
from app.adapter.chat.title import name_chat
from app.domain.transport import NetworkMode, Season
from app.usecase.chat import ChatContext, ChatEvent


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
