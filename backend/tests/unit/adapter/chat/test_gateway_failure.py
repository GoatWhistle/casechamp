import asyncio
from collections.abc import AsyncGenerator
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

from pydantic_ai import ModelRetry
from pydantic_ai.exceptions import UnexpectedModelBehavior

from app.adapter.chat.gateway import CodexResponsesGateway
from app.domain.transport import NetworkMode, Season
from app.usecase.chat import ChatContext, ChatEvent, ChatRequest


def test_tool_failure_retains_diagnostic_context() -> None:
    async def failed_run(*args: object) -> AsyncGenerator[ChatEvent, None]:
        yield ChatEvent("status", code="resolve_road_corridor")
        try:
            raise ModelRetry("No named road connects the requested endpoints")
        except ModelRetry as cause:
            raise UnexpectedModelBehavior("Tool retry limit reached") from cause

    gateway = CodexResponsesGateway.__new__(CodexResponsesGateway)
    gateway._slots = asyncio.Semaphore(3)
    gateway._codex = Mock()
    gateway._codex.account = AsyncMock(return_value=SimpleNamespace(account=object()))
    request = ChatRequest("Bridge closure", (), ChatContext(None, Season.SUMMER, NetworkMode.ROAD, "hansen"))
    provider = Mock()
    provider.client.close = AsyncMock()

    async def collect() -> list[ChatEvent]:
        return [event async for event in gateway.stream(request)]

    with (
        patch.object(gateway, "_run", failed_run),
        patch("app.adapter.chat.gateway.OpenAICodexProvider", return_value=provider),
        patch("app.adapter.log.stdlib.StdlibLogger.error") as logger,
    ):
        events = asyncio.run(collect())
    assert events[-1].code == "chat_provider_error"
    logger.assert_called_once()
    details = logger.call_args.kwargs
    assert details["stage"] == "resolve_road_corridor"
    assert details["error_type"] == "UnexpectedModelBehavior"
    assert details["reason"] == "No named road connects the requested endpoints"
    provider.client.close.assert_awaited_once()


def queued_gateway() -> CodexResponsesGateway:
    gateway = CodexResponsesGateway.__new__(CodexResponsesGateway)
    gateway._slots = asyncio.Semaphore(1)
    gateway._codex = Mock()
    gateway._codex.account = AsyncMock(return_value=SimpleNamespace(account=None))
    return gateway


def test_concurrent_question_waits_in_queue_instead_of_failing() -> None:
    gateway = queued_gateway()
    request = ChatRequest("Q", (), ChatContext(None, Season.SUMMER, NetworkMode.ROAD, "hansen"))

    async def scenario() -> list[str]:
        await gateway._slots.acquire()
        codes: list[str] = []

        async def consume() -> None:
            async for event in gateway.stream(request):
                codes.append(event.code)

        task = asyncio.create_task(consume())
        while not codes:
            await asyncio.sleep(0)
        gateway._slots.release()
        await task
        return codes

    codes = asyncio.run(scenario())
    assert codes[:2] == ["queued", "connecting"]
    assert "chat_busy" not in codes
    assert not gateway._slots.locked()


def test_long_queue_times_out_as_busy() -> None:
    gateway = queued_gateway()
    request = ChatRequest("Q", (), ChatContext(None, Season.SUMMER, NetworkMode.ROAD, "hansen"))

    async def scenario() -> list[str]:
        await gateway._slots.acquire()
        return [event.code async for event in gateway.stream(request)]

    with patch("app.adapter.chat.gateway.QUEUE_SECONDS", 0.01):
        assert asyncio.run(scenario()) == ["queued", "chat_busy"]
