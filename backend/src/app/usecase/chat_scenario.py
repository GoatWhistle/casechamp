from dataclasses import dataclass
from typing import Literal

ScenarioKind = Literal["speed", "slowdown", "closure", "roads", "connection", "links"]


@dataclass(frozen=True, slots=True)
class ScenarioCard:
    kind: ScenarioKind
    job_ids: list[str]


def road_kind(factors: list[float]) -> ScenarioKind:
    if not factors:
        return "roads"
    if all(factor == 0 for factor in factors):
        return "closure"
    if all(factor > 1 for factor in factors):
        return "speed"
    if all(0 < factor < 1 for factor in factors):
        return "slowdown"
    return "roads"
