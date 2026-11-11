from math import isfinite

from app.domain.errors import InvalidQuery
from app.usecase.road_records import RoadChange

ROAD_CLASSES = frozenset(
    {
        "motorway",
        "trunk",
        "primary",
        "secondary",
        "tertiary",
        "unclassified",
        "residential",
        "living_street",
        "service",
        "track",
        "road",
    }
)
SURFACES = frozenset(
    {
        "asphalt",
        "concrete",
        "paved",
        "gravel",
        "unpaved",
        "ground",
        "dirt",
        "compacted",
        "fine_gravel",
        "sand",
        "earth",
        "cobblestone",
        "paving_stones",
    }
)


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
            or not 0 <= change.speed_factor <= 3
        ):
            raise InvalidQuery("Speed factor must be between 0 (closure) and 3")
        if has_profile(change) and change.speed_factor != 1:
            raise InvalidQuery("Choose road profile changes or a manual speed factor")
        if change.lanes_total is not None and (
            isinstance(change.lanes_total, bool)
            or not isinstance(change.lanes_total, int)
            or not 1 <= change.lanes_total <= 32
        ):
            raise InvalidQuery("Total lane count must be an integer between 1 and 32")
        if change.highway is not None and change.highway not in ROAD_CLASSES:
            raise InvalidQuery("Unsupported road class")
        if change.surface is not None and change.surface not in SURFACES:
            raise InvalidQuery("Unsupported road surface")
        if change.speed_kmh is not None and (
            not isfinite(change.speed_kmh) or not 0 < change.speed_kmh <= 200
        ):
            raise InvalidQuery("Road speed must be finite and in (0,200] km/h")
