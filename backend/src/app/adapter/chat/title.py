from pydantic_ai import ModelRetry, RunContext

from app.adapter.chat.artifacts import ChatRun
from app.usecase.chat import ChatEvent

TITLE_INSTRUCTIONS = """Give this conversation a concise Russian title with name_chat before
answering the user. Use 3-7 words and at most 80 characters. Describe the concrete topic and intent
from the user's question and conversation, including a place or road when relevant. Do not copy
the whole question, add quotation marks, include private contact details, or use generic labels
like New chat or Transport analysis. Do not mention naming in your answer. Call name_chat once,
then continue the requested work normally."""


def name_chat(ctx: RunContext[ChatRun], title: str) -> str:
    if ctx.deps.title is not None:
        return "The chat already has a title. Continue answering the user's question."
    normalized = " ".join(title.split()).strip('"«». ')
    if not normalized or len(normalized) > 80:
        raise ModelRetry("Use a nonempty title of at most 80 characters.")
    ctx.deps.title = normalized
    ctx.deps.pending.append(ChatEvent("title", text=normalized))
    return "Title saved. Continue answering the user's question."
