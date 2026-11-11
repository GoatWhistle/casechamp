import json
import re
from contextvars import ContextVar
from time import monotonic
from typing import Any
from uuid import uuid4

from pydantic_ai.messages import FunctionToolCallEvent, FunctionToolResultEvent

from app.adapter.log.stdlib import StdlibLogger

request_id: ContextVar[str] = ContextVar("chat_request_id", default="")
SECRET_KEY = re.compile(r"authorization|cookie|password|secret|token|api[_-]?key", re.IGNORECASE)
SECRET_TEXT = re.compile(
    r"(?i)(bearer\s+)[\w.\-]+|\bsk-[\w\-]+|"
    r"((?:access_token|refresh_token|api_key|password|secret)\s*[=:]\s*)[^\s,;]+"
)


def safe_text(value: str, limit: int = 4000) -> str:
    return SECRET_TEXT.sub(lambda match: (match[1] or match[2] or "") + "<REDACTED>", value)[:limit]


def safe_payload(value: Any, depth: int = 0) -> Any:
    if depth > 8:
        return "<depth limit>"
    if isinstance(value, dict):
        return {
            str(key): "<REDACTED>" if SECRET_KEY.search(str(key)) else safe_payload(item, depth + 1)
            for key, item in list(value.items())[:60]
        }
    if isinstance(value, (list, tuple)):
        return [safe_payload(item, depth + 1) for item in value[:30]]
    if isinstance(value, str):
        try:
            decoded = json.loads(value)
        except (ValueError, TypeError):
            return safe_text(value)
        return safe_payload(decoded, depth + 1)
    if value is None or isinstance(value, (int, float, bool)):
        return value
    return safe_text(str(value))


def payload_text(value: Any) -> str:
    return json.dumps(safe_payload(value), ensure_ascii=False, default=str)[:4000]


class ChatTrace:
    def __init__(self) -> None:
        self.id = uuid4().hex
        self.started = monotonic()
        self.calls: dict[str, float] = {}
        self.tool_count = 0
        self.logger = StdlibLogger("uvicorn.error")

    def tool_call(self, event: FunctionToolCallEvent) -> None:
        part = event.part
        self.calls[part.tool_call_id] = monotonic()
        self.tool_count += 1
        self.logger.info(
            "chat_tool_started",
            request_id=self.id,
            tool=part.tool_name,
            tool_call_id=part.tool_call_id,
            arguments=payload_text(part.args),
        )

    def tool_result(self, event: FunctionToolResultEvent) -> None:
        part = event.part
        started = self.calls.pop(part.tool_call_id, None)
        self.logger.info(
            "chat_tool_finished",
            request_id=self.id,
            tool=part.tool_name,
            tool_call_id=part.tool_call_id,
            result_type=part.part_kind,
            elapsed_ms=round((monotonic() - started) * 1000) if started is not None else None,
            result=payload_text(part.content),
        )

    def finish(self, outcome: str) -> None:
        self.logger.info(
            "chat_request_finished",
            request_id=self.id,
            outcome=outcome,
            elapsed_ms=round((monotonic() - self.started) * 1000),
            tool_count=self.tool_count,
        )
