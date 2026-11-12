from dataclasses import dataclass

from app.domain.normative.model import AccessRow


@dataclass(frozen=True, slots=True)
class RouteComparison:
    unit: str
    paired_paths: int
    increased: int
    decreased: int
    unchanged: int
    lost: int
    restored: int
    unresolved: int
    mean_change: float | None
    max_increase: float | None


def compare_routes(before: list[AccessRow], after: list[AccessRow], unit: str) -> RouteComparison:
    baseline = {row.id: row for row in before}
    if (
        len(baseline) != len(before)
        or set(baseline) != {row.id for row in after}
        or len(before) != len(after)
    ):
        raise ValueError("Route comparison requires equal unique origin sets")
    increased = decreased = unchanged = lost = restored = unresolved = 0
    differences: list[float] = []
    for row in after:
        first = baseline[row.id]
        old = first.distance_metres if unit == "metres" else first.minutes
        new = row.distance_metres if unit == "metres" else row.minutes
        if old is None and new is None:
            unresolved += 1
        elif old is None:
            restored += 1
        elif new is None:
            lost += 1
        else:
            delta = new - old
            differences.append(delta)
            if delta > 1e-6:
                increased += 1
            elif delta < -1e-6:
                decreased += 1
            else:
                unchanged += 1
    return RouteComparison(
        unit,
        len(differences),
        increased,
        decreased,
        unchanged,
        lost,
        restored,
        unresolved,
        sum(differences) / len(differences) if differences else None,
        max([value for value in differences if value > 1e-6], default=None),
    )
