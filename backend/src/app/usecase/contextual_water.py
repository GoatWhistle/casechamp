from dataclasses import dataclass
from typing import Protocol

from app.usecase.dto import BoundaryShape


@dataclass(frozen=True, slots=True)
class ContextualWater:
    id: str
    name: str
    bounds: tuple[float, float, float, float]
    polygons: list[list[list[tuple[float, float]]]]
    source_url: str
    observed_at: str
    source_sha256: str
    osm_relation_id: int
    geometry_basis: str
    display_only: bool = True
    analytics_enabled: bool = False

    def shape(self) -> BoundaryShape:
        return BoundaryShape(self.id, self.name, self.bounds, self.polygons)


class ContextualWaterRepository(Protocol):
    def boundaries(self) -> list[ContextualWater]: ...
