from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class PedestrianNetwork:
    revision: str
    nodes: list[tuple[int, float, float]]
    edges: list[tuple[int, int, float, int]]
    source_url: str
    source_timestamp: str


class PedestrianRepository(Protocol):
    def network(self, revision: str | None = None) -> PedestrianNetwork: ...
