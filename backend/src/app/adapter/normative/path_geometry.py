from typing import Any

from app.domain.errors import DataUnavailable
from app.domain.normative.model import Facility, Origin
from app.usecase.normative.route import RouteGeometry


def predecessor_path(predecessors: Any, start: int, end: int) -> list[int]:
    path = [end]
    while path[-1] != start:
        node = int(predecessors[path[-1]])
        if node < 0 or len(path) > len(predecessors):
            raise DataUnavailable("The saved route cannot be reconstructed")
        path.append(node)
    return list(reversed(path))


def geometry(
    points: list[tuple[float, float]],
    origin: Origin,
    facility: Facility,
    minutes: float | None = None,
    metres: float | None = None,
) -> RouteGeometry:
    if not points or origin.latitude is None or origin.longitude is None:
        raise DataUnavailable("Origin coordinates are unavailable")
    if facility.latitude is None or facility.longitude is None:
        raise DataUnavailable("Facility coordinates are unavailable")
    return RouteGeometry(
        points,
        [
            [(origin.longitude, origin.latitude), points[0]],
            [points[-1], (facility.longitude, facility.latitude)],
        ],
        minutes,
        metres,
    )
