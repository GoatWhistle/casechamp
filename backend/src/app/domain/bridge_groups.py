from dataclasses import dataclass
from itertools import pairwise
from math import cos, hypot, radians


@dataclass(frozen=True)
class BridgePart:
    way_id: int
    name: str
    reference: str
    highway: str
    length_km: float
    source: int
    target: int
    coordinates: list[list[float]]


def distance_km(a: list[float], b: list[float]) -> float:
    return 111.195 * hypot((a[0] - b[0]) * cos(radians((a[1] + b[1]) / 2)), a[1] - b[1])


def distance_to_line_km(point: list[float], line: list[list[float]]) -> float:
    scale = cos(radians(point[1]))
    closest = float("inf")
    for a, b in pairwise(line):
        ax, ay = (a[0] - point[0]) * scale, a[1] - point[1]
        dx, dy = (b[0] - a[0]) * scale, b[1] - a[1]
        squared = dx * dx + dy * dy
        fraction = max(0.0, min(1.0, -(ax * dx + ay * dy) / squared)) if squared else 0.0
        closest = min(closest, 111.195 * hypot(ax + fraction * dx, ay + fraction * dy))
    return closest


def parallel_parts(a: BridgePart, b: BridgePart) -> bool:
    if not (a.reference or a.name) or (a.reference, a.name, a.highway) != (
        b.reference,
        b.name,
        b.highway,
    ):
        return False
    a0, a1 = a.coordinates[0], a.coordinates[-1]
    b0, b1 = b.coordinates[0], b.coordinates[-1]
    span = min(distance_km(a0, a1), distance_km(b0, b1))
    tolerance = min(0.08, span / 4)
    return (
        tolerance > 0
        and min(
            max(distance_km(a0, b0), distance_km(a1, b1)),
            max(distance_km(a0, b1), distance_km(a1, b0)),
        )
        <= tolerance
    )


def bridge_groups(parts: list[BridgePart]) -> list[list[BridgePart]]:
    parents = list(range(len(parts)))

    def root(index: int) -> int:
        while parents[index] != index:
            parents[index] = parents[parents[index]]
            index = parents[index]
        return index

    for i, a in enumerate(parts):
        for j in range(i):
            b = parts[j]
            if (
                a.way_id == b.way_id
                or {a.source, a.target} & {b.source, b.target}
                or parallel_parts(a, b)
            ):
                parents[root(i)] = root(j)
    groups: dict[int, list[BridgePart]] = {}
    for i, part in enumerate(parts):
        groups.setdefault(root(i), []).append(part)
    return list(groups.values())
