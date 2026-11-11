from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class RoadGeometry:
    names: list[str]
    length_km: float
    lines: list[list[list[float]]]


class RoadGeometrySource(Protocol):
    def geometry(self, way_ids: list[int]) -> RoadGeometry: ...
