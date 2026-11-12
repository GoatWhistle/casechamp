from typing import Protocol

from app.domain.normative.scenario_index import ScenarioIndex


class ScenarioIndexRepository(Protocol):
    def latest(self, region_id: str, criterion_id: str) -> ScenarioIndex | None: ...
    def regions(self, criterion_id: str) -> list[ScenarioIndex]: ...
