import traceback

from pydantic_ai import ModelRetry
from pydantic_ai.messages import FunctionToolResultEvent, RetryPromptPart

from app.adapter.chat.trace import request_id, safe_text
from app.adapter.log.stdlib import StdlibLogger
from app.domain.errors import DomainError
from app.usecase.chat import ChatEvent


def chat_failure(error: BaseException, code: str, stage: str) -> ChatEvent:
    reason = ""
    cause: BaseException | None = error
    seen: set[int] = set()
    causes: list[str] = []
    while cause is not None and id(cause) not in seen and len(causes) < 8:
        seen.add(id(cause))
        causes.append(f"{type(cause).__name__}: {safe_text(str(cause), 500)}")
        if isinstance(cause, (DomainError, ModelRetry)):
            reason = str(cause)[:500]
        cause = cause.__cause__ or cause.__context__
    status = getattr(error, "status_code", None)
    frames = traceback.extract_tb(error.__traceback__)
    StdlibLogger("uvicorn.error").error(
        "chat_request_failed",
        request_id=request_id.get(),
        code=code,
        stage=stage,
        error_type=type(error).__name__,
        reason=safe_text(reason),
        message=safe_text(str(error)),
        causes=" | ".join(causes),
        traceback=" | ".join(f"{frame.filename}:{frame.lineno}:{frame.name}" for frame in frames),
        status_code=status if isinstance(status, int) else None,
    )
    return ChatEvent("error", code=code)


def tool_outcome(event: FunctionToolResultEvent) -> None:
    part = event.part
    content = str(getattr(part, "content", ""))
    if isinstance(part, RetryPromptPart) or '"status": "unresolved"' in content:
        StdlibLogger("uvicorn.error").warning(
            "chat_tool_rejected",
            request_id=request_id.get(),
            tool=part.tool_name,
            reason=safe_text(content, 500),
        )
