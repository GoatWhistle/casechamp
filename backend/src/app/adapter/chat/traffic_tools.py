import json
from dataclasses import replace

from pydantic_ai import ModelRetry, RunContext

from app.adapter.chat.artifacts import ChatRun
from app.domain.errors import DomainError
from app.usecase.chat import ChatEvent
from app.usecase.traffic import TrafficJob, TrafficPort, TrafficScope
from app.usecase.traffic_presentation import traffic_brief


def traffic_reply(job: TrafficJob) -> str:
    return json.dumps(traffic_brief(job), ensure_ascii=False)


def traffic_event(job: TrafficJob) -> ChatEvent:
    compact = replace(
        job, roads=[], zones=[], alternatives=[replace(row, roads=[]) for row in job.alternatives]
    )
    return ChatEvent("traffic", traffic=compact)


class TrafficTools:
    def __init__(self, traffic: TrafficPort | None) -> None:
        self.traffic = traffic

    def available(self) -> TrafficPort:
        if self.traffic is None:
            raise ModelRetry("Housing-derived traffic calculations are unavailable")
        return self.traffic

    def calculate(self, ctx: RunContext[ChatRun], scope: TrafficScope) -> str:
        try:
            job = self.available().submit(scope)
        except DomainError as error:
            raise ModelRetry(error.message) from error
        ctx.deps.pending.append(traffic_event(job))
        return traffic_reply(job)

    def inspect(self, ctx: RunContext[ChatRun], job_id: str, cancel: bool = False) -> str:
        try:
            job = self.available().cancel(job_id) if cancel else self.available().get(job_id)
        except DomainError as error:
            raise ModelRetry(error.message) from error
        ctx.deps.pending.append(traffic_event(job))
        return traffic_reply(job)
