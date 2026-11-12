from typing import Protocol, runtime_checkable

from app.domain.errors import DataUnavailable, RegionNotFound
from app.usecase.interface import AtlasRepository
from app.usecase.road_records import RoadView


@runtime_checkable
class SelectedRoadViewSource(Protocol):
    def view_selected(
        self,
        bounds: tuple[float, float, float, float],
        zoom: float,
        selected_bounds: tuple[float, float, float, float],
    ) -> RoadView: ...


def selected_view(
    source: object,
    atlas: AtlasRepository,
    bounds: tuple[float, float, float, float],
    zoom: float,
    region_id: str,
) -> RoadView:
    boundary = next((b for b in atlas.boundaries() if b.id == region_id), None)
    if boundary is None:
        raise RegionNotFound()
    if not isinstance(source, SelectedRoadViewSource):
        raise DataUnavailable("Selected-region road detail is unavailable")
    return source.view_selected(bounds, zoom, boundary.bounds)
