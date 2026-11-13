from dataclasses import dataclass
from typing import Literal, Protocol


@dataclass(frozen=True)
class WalkingPoint:
    id: str
    latitude: float | None
    longitude: float | None
    attachment_limit_metres: float


@dataclass(frozen=True)
class WalkingLink:
    source: str
    target: str
    status: Literal['available', 'unattached', 'outside_walking_limit']
    metres: float | None
    seconds: int | None


class TransitWalkingPort(Protocol):
    @property
    def speed(self) -> float: ...
    @property
    def revision(self) -> str: ...
    def measure(self, points: list[WalkingPoint], pairs: list[tuple[str, str]],
                maximum_metres: float) -> list[WalkingLink]: ...
