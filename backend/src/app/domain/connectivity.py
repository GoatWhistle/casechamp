from dataclasses import dataclass
from math import isfinite
from typing import Literal

from app.domain.errors import InvalidQuery

RouteStatus = Literal["reachable", "unreachable", "unbound"]


@dataclass(frozen=True)
class PairAccess:
    status: RouteStatus
    hours: float | None


def pair_score(access: PairAccess) -> float | None:
    if access.status == "unbound":
        return None
    if access.status == "unreachable":
        return 0.0
    if access.hours is None or not isfinite(access.hours) or access.hours < 0:
        raise InvalidQuery("Reachable pairs require finite nonnegative travel hours")
    return 100 * 2 ** (-access.hours / 2)


def group_score(pairs: list[PairAccess]) -> float | None:
    if not pairs:
        raise InvalidQuery("Connectivity requires at least one pair")
    values = [pair_score(pair) for pair in pairs]
    if any(value is None for value in values):
        return None
    return sum(value for value in values if value is not None) / len(values)
