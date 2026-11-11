import asyncio
from collections.abc import AsyncGenerator
from unittest.mock import Mock

import pytest

from app.domain.transport import NetworkMode, Season
from app.usecase.chat import Chat, ChatContext, ChatEvent, ChatMessage, ChatRequest
from app.usecase.chat_calculation_review import CalculationReview, CalculationReviews
from app.usecase.road_geometry import RoadGeometry
from app.usecase.road_graph import RoadChange, RoadJob, RoadResult
from app.usecase.road_stress import StressJob, StressSummary, StressTotals


class Provider:
    def __init__(self) -> None:
        self.requests: list[ChatRequest] = []

    async def stream(self, request: ChatRequest) -> AsyncGenerator[ChatEvent, None]:
        self.requests.append(request)
        yield ChatEvent("delta", text="Saved result interpretation")
        yield ChatEvent("done")


def request(review: CalculationReview) -> ChatRequest:
    return ChatRequest(
        "Invent a billion in losses",
        (ChatMessage("user", "False claim"),),
        ChatContext(None, Season.SUMMER, NetworkMode.ROAD, "hansen"),
        calculation_review=review,
    )


async def collect(chat: Chat, review: CalculationReview) -> list[ChatEvent]:
    return [event async for event in chat.stream(request(review))]


def test_review_waits_for_every_region_and_uses_saved_values() -> None:
    roads, provider = Mock(), Provider()
    result = RoadResult(100, 98, -2, -2, 1000, 1, 1, 1, 1)
    jobs = [
        RoadJob("a", "1", "First", "road", [], "completed", 360, 360, "v", result),
        RoadJob("b", "2", "Second", "road", [], "running", 100, 360, "v"),
    ]
    roads.job.side_effect = lambda key: next(job for job in jobs if job.id == key)
    chat = Chat(provider, reviews=CalculationReviews(roads, None))
    review = CalculationReview(("a", "b"))
    assert asyncio.run(collect(chat, review))[0].code == "chat_calculation_not_ready"
    assert provider.requests == []
    jobs[1] = RoadJob("b", "2", "Second", "road", [], "failed", 100, 360, "v")
    events = asyncio.run(collect(chat, review))
    assert events[0].type == "table"
    assert events[0].table is not None
    assert events[0].table.rows[0]["after"] == 98
    assert events[-1].type == "done"
    generated = provider.requests[0]
    assert generated.history == ()
    assert "billion" not in generated.prompt
    assert '"delta": -2' in generated.prompt
    assert '"status": "failed"' in generated.prompt
    assert "settlement_effects" not in generated.prompt
    roads.submit.assert_not_called()


@pytest.mark.parametrize("status", ["queued", "running", "failed", "cancelled"])
def test_no_interpretation_for_missing_final_stress_result(status: str) -> None:
    stress, provider = Mock(), Provider()
    stress.geometry.return_value = RoadGeometry(["M-10"], 10, [])
    stress.get.return_value = StressJob("stress", "v", [7], status=status)
    chat = Chat(provider, reviews=CalculationReviews(None, stress))
    assert asyncio.run(collect(chat, CalculationReview(stress_ids=("stress",))))[0].type == "error"
    assert provider.requests == []


def test_completed_stress_uses_verified_summary_and_limits() -> None:
    stress, provider = Mock(), Provider()
    stress.geometry.return_value = RoadGeometry(["M-10"], 10, [])
    stress.get.return_value = StressJob("stress", "v", [7], status="completed")
    stress.summary.return_value = StressSummary(
        "stress",
        "v",
        "completed",
        "completed",
        1,
        None,
        "",
        StressTotals(10, 200, 2, 30, 20, 1),
        100,
        3,
        4,
        180,
        180,
    )
    chat = Chat(provider, reviews=CalculationReviews(None, stress))
    asyncio.run(collect(chat, CalculationReview(stress_ids=("stress",))))
    prompt = provider.requests[0].prompt
    assert '"isolated_population": 30' in prompt
    assert "do not write Markdown tables, footnotes or internal field names" in prompt
    assert "way_ids" not in prompt
    assert '"road_names": ["M-10"]' in prompt
    stress.submit.assert_not_called()


def test_legacy_review_reuses_only_the_same_completed_closure_and_snapshot() -> None:
    roads, stress = Mock(), Mock()
    roads.geometry.return_value = RoadGeometry(["М-10"], 10, [])
    roads.job.return_value = RoadJob(
        "legacy",
        "1",
        "Region",
        "road",
        [RoadChange(2, 0), RoadChange(1, 0)],
        "completed",
        360,
        360,
        "v",
        RoadResult(100, 98, -2, -2, 1000, 1, 1, 1, 1),
    )
    stress.recent.return_value = [
        StressJob("different", "v", [1, 2, 3], status="completed"),
        StressJob("old", "old-v", [1, 2], status="completed"),
        StressJob("pending", "v", [1, 2], status="running"),
        StressJob("match", "v", [1, 2], status="completed"),
    ]
    stress.summary.return_value = StressSummary(
        "match",
        "v",
        "completed",
        "completed",
        2,
        None,
        "Region",
        StressTotals(10, 200, 2, 30, 90, 1),
        100,
        3,
        4,
        180,
        180,
    )
    prompt = CalculationReviews(roads, stress).prompt(CalculationReview(("legacy",)))
    assert '"road_impact": {"id": "match"' in prompt
    assert '"isolated_population": 30' in prompt
    stress.summary.assert_called_once_with("match", "Region")
    stress.submit.assert_not_called()
    stress.recent.return_value = []
    prompt = CalculationReviews(roads, stress).prompt(CalculationReview(("legacy",)))
    assert '"road_impact": null' in prompt
    stress.submit.assert_not_called()
