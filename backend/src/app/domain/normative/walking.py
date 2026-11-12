from collections.abc import Mapping
from math import asin, cos, radians, sin, sqrt

WALKABLE = frozenset(
    {
        "residential",
        "living_street",
        "service",
        "unclassified",
        "tertiary",
        "tertiary_link",
        "secondary",
        "secondary_link",
        "primary",
        "primary_link",
        "road",
        "track",
        "path",
        "footway",
        "pedestrian",
        "steps",
        "bridleway",
        "cycleway",
    }
)
ALLOWED_FOOT = frozenset({"yes", "designated", "permissive", "official"})
DENIED = frozenset({"no", "private", "destination", "customers", "delivery"})
RESIDENTIAL = frozenset(
    {"apartments", "residential", "house", "detached", "semidetached_house", "terrace", "dormitory"}
)


def walkable(tags: Mapping[str, str]) -> bool:
    if tags.get("highway") not in WALKABLE or tags.get("area") == "yes":
        return False
    if any(key in tags for key in ("foot:conditional", "access:conditional")):
        return False
    foot = tags.get("foot", "")
    if foot in DENIED or foot == "use_sidepath":
        return False
    if foot in ALLOWED_FOOT:
        return True
    return tags.get("access", "") not in DENIED and tags.get("highway") != "cycleway"


def blocked_node(tags: Mapping[str, str]) -> bool:
    if "barrier" in tags and tags.get("locked") == "yes":
        return True
    if tags.get("foot") in ALLOWED_FOOT:
        return False
    return tags.get("foot") in DENIED or (
        "barrier" in tags and (tags.get("access") in DENIED or tags.get("locked") == "yes")
    )


def walking_directions(tags: Mapping[str, str]) -> tuple[bool, bool]:
    value = tags.get("oneway:foot", "no")
    if value in {"yes", "1", "true"}:
        return True, False
    if value == "-1":
        return False, True
    return True, True


def residential(tags: Mapping[str, str]) -> bool:
    return tags.get("building") in RESIDENTIAL or (
        tags.get("building") == "yes" and tags.get("building:use") == "residential"
    )


def metres_between(a: tuple[float, float], b: tuple[float, float]) -> float:
    lon1, lat1, lon2, lat2 = map(radians, (*a, *b))
    value = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 12_742_000 * asin(min(1, sqrt(value)))
