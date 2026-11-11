import asyncio
import logging
from collections.abc import AsyncGenerator
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

import pytest
from pydantic_ai.exceptions import UnexpectedModelBehavior
from pydantic_ai.messages import (
    FunctionToolCallEvent,
    FunctionToolResultEvent,
    ToolCallPart,
    ToolReturnPart,
)

from app.adapter.chat.gateway import CodexResponsesGateway
from app.adapter.chat.trace import ChatTrace, payload_text, request_id
from app.domain.transport import NetworkMode, Season
from app.usecase.chat import ChatContext, ChatEvent, ChatRequest


def test_stream_failure_has_correlated_start_exception_and_end(
    caplog: pytest.LogCaptureFixture,
) -> None:
    async def failed_run(*args: object) -> AsyncGenerator[ChatEvent, None]:
        yield ChatEvent("status", code="manage_calculation")
        raise UnexpectedModelBehavior("Tool retry limit reached")

    gateway = CodexResponsesGateway.__new__(CodexResponsesGateway)
    gateway._slots = asyncio.Semaphore(3)
    gateway._codex = Mock()
    gateway._codex.account = AsyncMock(return_value=SimpleNamespace(account=object()))
    provider = Mock()
    provider.client.close = AsyncMock()
    request = ChatRequest(
        "Москва — Петербург", (), ChatContext(None, Season.SUMMER, NetworkMode.ROAD, "hansen")
    )

    async def collect() -> list[ChatEvent]:
        return [event async for event in gateway.stream(request)]

    with (
        caplog.at_level(logging.INFO, logger="uvicorn.error"),
        patch.object(gateway, "_run", failed_run),
        patch("app.adapter.chat.gateway.OpenAICodexProvider", return_value=provider),
    ):
        events = asyncio.run(collect())
    assert events[-1].type == "error"
    messages = [record.message for record in caplog.records]
    assert any("chat_request_started" in message for message in messages)
    assert any(
        "chat_request_failed" in message and "Tool retry limit reached" in message
        for message in messages
    )
    assert any(
        "chat_request_finished" in message and "outcome='chat_provider_error'" in message
        for message in messages
    )
    ids = {
        message.split("request_id='")[1].split("'")[0]
        for message in messages
        if "chat_request_" in message
    }
    assert len(ids) == 1
    assert request_id.get() == ""


def test_tools_keep_call_ids_skill_names_and_result_without_credentials(
    caplog: pytest.LogCaptureFixture,
) -> None:
    trace = ChatTrace()
    with caplog.at_level(logging.INFO, logger="uvicorn.error"):
        trace.tool_call(
            FunctionToolCallEvent(
                ToolCallPart(
                    "load_skill",
                    {"name": "settlement-connectivity", "api_key": "private-key"},
                    "call-1",
                )
            )
        )
        trace.tool_result(
            FunctionToolResultEvent(
                ToolReturnPart(
                    "load_skill",
                    {"calculation_id": "saved-pair", "token": "private-token"},
                    "call-1",
                )
            )
        )
    assert trace.tool_count == 1
    assert not trace.calls
    assert all(f"request_id='{trace.id}'" in record.message for record in caplog.records)
    text = caplog.text
    assert "settlement-connectivity" in text
    assert "saved-pair" in text
    assert "call-1" in text
    assert "elapsed_ms=" in text
    assert "private-key" not in text
    assert "private-token" not in text


def test_serialized_credentials_are_redacted_before_truncation() -> None:
    result = payload_text('{"nested":{"Authorization":"Bearer private", "password":"hidden"}}')
    assert "private" not in result
    assert "hidden" not in result
    assert "REDACTED" in result
    assert "sensitive" not in payload_text("Bearer sensitive")
    assert len(payload_text("x" * 10000)) <= 4000
