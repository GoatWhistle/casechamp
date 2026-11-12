from math import isfinite

from app.domain.errors import InvalidQuery
from app.usecase.road_records import RoadChange


def has_profile(change: RoadChange) -> bool:
    return any(
        value is not None
        for value in (
            change.lanes_total,
            change.highway,
            change.surface,
            change.speed_kmh,
        )
    )


def validate_changes(changes: list[RoadChange]) -> None:
    for change in changes:
        if (
            change.way_id < 0
            or not isfinite(change.speed_factor)
            or change.speed_factor not in (0, 1)
        ):
            raise InvalidQuery("Standalone speed changes are not supported; use closure or added lanes")
        if has_profile(change) and change.speed_factor != 1:
            raise InvalidQuery("Choose road profile changes or a manual speed factor")
        if change.lanes_total is not None and (
            isinstance(change.lanes_total, bool)
            or not isinstance(change.lanes_total, int)
            or not 1 <= change.lanes_total <= 32
        ):
            raise InvalidQuery("Total lane count must be an integer between 1 and 32")
        if any(value is not None for value in (change.highway, change.surface, change.speed_kmh)):
            raise InvalidQuery("Existing road interventions support added lanes, not speed overrides")
