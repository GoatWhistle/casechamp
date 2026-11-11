import json
from dataclasses import asdict

from pydantic_ai import ModelRetry, RunContext

from app.adapter.chat.artifacts import ChatRun
from app.domain.errors import DomainError
from app.usecase.chat import ChatEvent
from app.usecase.road_analysis import AnalysisJob, AnalysisMode, RoadAnalysis


class AnalysisTools:
    def __init__(self, analysis: RoadAnalysis) -> None:
        self.analysis = analysis

    def start_road_analysis(
        self, ctx: RunContext[ChatRun], region_id: str, mode: AnalysisMode, percent: int = 20
    ) -> str:
        try:
            job = self.analysis.submit(region_id, mode, percent)
            return self._display(ctx, job)
        except DomainError as error:
            raise ModelRetry(error.message) from error

    def read_road_analysis(self, ctx: RunContext[ChatRun], analysis_id: str) -> str:
        try:
            return self._display(ctx, self.analysis.get(analysis_id))
        except DomainError as error:
            raise ModelRetry(error.message) from error

    def control_road_analysis(self, ctx: RunContext[ChatRun], analysis_id: str, action: str) -> str:
        if action not in {"continue", "cancel"}:
            raise ModelRetry("Choose continue or cancel")
        try:
            job = (
                self.analysis.resume(analysis_id)
                if action == "continue"
                else self.analysis.cancel(analysis_id)
            )
            return self._display(ctx, job)
        except DomainError as error:
            raise ModelRetry(error.message) from error

    def _display(self, ctx: RunContext[ChatRun], job: AnalysisJob) -> str:
        ctx.deps.pending.append(ChatEvent("analysis", analysis=job))
        return json.dumps({"analysis": asdict(job), "display": "inline_chat_ranking"}, ensure_ascii=False)
