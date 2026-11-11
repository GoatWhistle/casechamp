import json
from collections.abc import AsyncIterator
from contextlib import aclosing
from dataclasses import asdict
from typing import Literal
from urllib.parse import urlsplit

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel, Field

from app.controller.road_analysis.schemas import AnalysisResponse
from app.domain.transport import NetworkMode, Season
from app.usecase.chat import Chat, ChatContext, ChatMessage, ChatRequest
from app.usecase.chat_artifacts import ChatChart, ChatTable, ScenarioCard
from app.usecase.chat_calculation_review import CalculationReview
from app.usecase.chat_map import ChatMapCommand
from app.usecase.road_corridor import CorridorCalculation
from app.usecase.road_stress import StressJob, StressRouteComparison


class ChatMessageInput(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(min_length=1, max_length=12000)


class ChatContextInput(BaseModel):
    region_id: str | None = Field(default=None, max_length=64)
    season: Season = Season.SUMMER
    network_mode: NetworkMode = NetworkMode.ROAD
    metric: str = Field(default="hansen", max_length=64)
    road_way_ids: list[int] = Field(default_factory=list, max_length=50)
    stress_job_id: str | None = Field(default=None, max_length=128)
    stress_point_id: str | None = Field(default=None, max_length=128)


class CalculationReviewInput(BaseModel):
    scenario_ids: list[str] = Field(default_factory=list, max_length=12)
    stress_ids: list[str] = Field(default_factory=list, max_length=12)


class ChatInput(BaseModel):
    prompt: str = Field(min_length=1, max_length=4000, pattern=r"\S")
    history: list[ChatMessageInput] = Field(default_factory=list, max_length=12)
    context: ChatContextInput = Field(default_factory=ChatContextInput)
    analysis_id: str | None = Field(default=None, min_length=1, max_length=128)
    calculation_review: CalculationReviewInput | None = None


class ChatStreamEvent(BaseModel):
    type: Literal["status", "delta", "done", "error", "table", "chart", "map", "calculation", "analysis", "stress_test", "scenario"]
    text: str = ""
    code: str = ""
    table: ChatTable | None = None
    chart: ChatChart | None = None
    scenario: ScenarioCard | None = None
    map: ChatMapCommand | None = None
    stress_route: StressRouteComparison | None = None
    stress_test: StressJob | None = None
    calculation: CorridorCalculation | None = None
    analysis: AnalysisResponse | None = None


def build_chat_router(chat: Chat) -> APIRouter:
    router = APIRouter(tags=["chat"])

    @router.post("/chat/calculation-tables", response_model=list[ChatTable])
    def calculation_tables(body: CalculationReviewInput) -> list[ChatTable]:
        return chat.comparison_tables(CalculationReview(tuple(body.scenario_ids), tuple(body.stress_ids)))

    @router.post("/chat/calculation-review", response_model=ChatStreamEvent)
    @router.post(
        "/chat",
        response_model=ChatStreamEvent,
        responses={200: {"content": {"application/x-ndjson": {}}}},
    )
    async def stream_chat(body: ChatInput, request: Request) -> StreamingResponse | JSONResponse:
        if request.url.path.endswith("/calculation-review") and body.calculation_review is None:
            return JSONResponse({"code": "invalid_query", "message": "Calculation review IDs required"}, 422)
        local_hosts = {"localhost", "127.0.0.1", "::1", "testserver"}
        origin = request.headers.get("origin")
        if request.url.hostname not in local_hosts or (
            origin and urlsplit(origin).hostname not in local_hosts
        ):
            return JSONResponse({"code": "chat_local_only", "message": "Local chat only"}, 403)
        command = ChatRequest(
            body.prompt,
            tuple(ChatMessage(message.role, message.content) for message in body.history),
            ChatContext(
                body.context.region_id,
                body.context.season,
                body.context.network_mode,
                body.context.metric,
                tuple(body.context.road_way_ids),
                body.context.stress_job_id,
                body.context.stress_point_id,
            ),
            body.analysis_id,
            CalculationReview(tuple(body.calculation_review.scenario_ids),
                              tuple(body.calculation_review.stress_ids))
            if body.calculation_review else None,
        )

        async def events() -> AsyncIterator[str]:
            async with aclosing(chat.stream(command)) as stream:
                async for event in stream:
                    if await request.is_disconnected():
                        break
                    yield json.dumps(asdict(event), ensure_ascii=False) + "\n"

        return StreamingResponse(
            events(),
            media_type="application/x-ndjson",
            headers={
                "Cache-Control": "no-cache, no-store",
                "X-Accel-Buffering": "no",
            },
        )

    return router
