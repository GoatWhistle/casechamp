from dataclasses import dataclass
from math import isfinite

import numpy as np
from shapely import STRtree, points
from shapely.affinity import translate
from shapely.geometry import Polygon

from app.domain.normative.model import AccessRow
from app.usecase.municipalities import Municipality


def _ring(
    ring: list[tuple[float, float]], anchor: float | None = None
) -> list[tuple[float, float]]:
    result: list[tuple[float, float]] = []
    for longitude, latitude in ring:
        previous = result[-1][0] if result else anchor
        if previous is not None:
            longitude += 360 * round((previous - longitude) / 360)
        result.append((longitude, latitude))
    return result


@dataclass(frozen=True, slots=True)
class MunicipalAssignment:
    rows: dict[str, list[AccessRow]]
    assigned: int
    ambiguous: int
    outside: int
    coordinates_missing: int


class MunicipalSpatialIndex:
    def __init__(self, municipalities: list[Municipality]) -> None:
        self.identifiers = [item.id for item in municipalities]
        geometries = []
        self.owners: list[str] = []
        for municipality in municipalities:
            for rings in municipality.coordinates:
                exterior = _ring(rings[0])
                anchor = sum(point[0] for point in exterior) / len(exterior)
                polygon = Polygon(exterior, [_ring(ring, anchor) for ring in rings[1:]])
                if not polygon.is_valid:
                    raise ValueError("Original municipal polygon is invalid: " + municipality.id)
                for shift in (-360, 0, 360):
                    geometries.append(translate(polygon, xoff=shift))
                    self.owners.append(municipality.id)
        self.tree = STRtree(geometries)

    def assign(self, rows: list[AccessRow]) -> MunicipalAssignment:
        valid = [
            row
            for row in rows
            if row.longitude is not None
            and row.latitude is not None
            and isfinite(row.longitude)
            and isfinite(row.latitude)
        ]
        coordinates = np.array(
            [(((row.longitude or 0) + 180) % 360 - 180, row.latitude) for row in valid]
        ).reshape(-1, 2)
        matches = self.tree.query(points(coordinates), predicate="covered_by")
        owners: dict[int, set[str]] = {}
        for source, target in zip(matches[0], matches[1], strict=True):
            owners.setdefault(int(source), set()).add(self.owners[int(target)])
        selected: dict[str, list[AccessRow]] = {identifier: [] for identifier in self.identifiers}
        ambiguous = 0
        for position, identifiers in owners.items():
            if len(identifiers) != 1:
                ambiguous += 1
                continue
            selected[next(iter(identifiers))].append(valid[position])
        count = sum(len(values) for values in selected.values())
        return MunicipalAssignment(
            selected, count, ambiguous, len(valid) - count - ambiguous, len(rows) - len(valid)
        )
