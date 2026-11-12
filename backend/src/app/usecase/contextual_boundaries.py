from dataclasses import dataclass
from typing import Protocol

from app.usecase.dto import BoundaryShape


@dataclass(frozen=True, slots=True)
class ContextualBoundary:
    id: str
    name: str
    bounds: tuple[float, float, float, float]
    polygons: list[list[list[tuple[float, float]]]]
    source_url: str
    observed_at: str
    source_sha256: str
    source_name: str
    source_iso: str
    source_shape_id: str
    geometry_basis: str
    disputed_status: str
    display_only: bool = True
    analytics_enabled: bool = False
    contested: bool = True

    def shape(self) -> BoundaryShape:
        return BoundaryShape(self.id, self.name, self.bounds, self.polygons)


class ContextualBoundaryRepository(Protocol):
    def boundaries(self) -> list[ContextualBoundary]: ...
