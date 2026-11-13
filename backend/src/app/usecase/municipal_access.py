import json
from collections.abc import Callable
from dataclasses import dataclass
from math import ceil, isfinite
from threading import Lock

from app.domain.errors import DataUnavailable, InvalidQuery
from app.domain.municipal_metrics import municipal_contains
from app.domain.normative.model import AccessRow, Facility
from app.domain.normative.scenario_index import SCENARIO_THRESHOLDS, scenario_policy
from app.usecase.municipal_dataset import MunicipalSnapshotSource, municipal_boundary_digest
from app.usecase.municipalities import Municipality, MunicipalityQueries


@dataclass(frozen=True, slots=True)
class MunicipalAccessSnapshot:
    sha256: str
    source: MunicipalSnapshotSource
    rows: list[AccessRow]


@dataclass(frozen=True, slots=True)
class MunicipalAccessPoint:
    row: AccessRow
    facility: Facility | None
    deficit: bool


@dataclass(frozen=True, slots=True)
class MunicipalAccessResult:
    region_id: str
    municipality_id: str
    criterion_id: str
    source_sha256: str
    run_id: str
    measured_at: str
    unit: str
    mode: str
    threshold: float
    reference_points: int
    measured_points: int
    unreachable_points: int
    unresolved_points: int
    deficit_points: int
    p90: float | None
    worst_decile_mean: float | None
    points: list[MunicipalAccessPoint]
    total: int
    offset: int
    limit: int
    legal_compliance_confirmed: bool = False
    percentile_basis: str = "finite_reference_points_nearest_rank"


class MunicipalAccessQueries:
    def __init__(
        self,
        municipalities: MunicipalityQueries,
        snapshot: Callable[[Municipality, str], MunicipalAccessSnapshot | None],
        facilities: Callable[[str, set[str]], list[Facility]],
    ) -> None:
        self.municipalities = municipalities
        self.snapshot = snapshot
        self.facilities = facilities
        self._selection: tuple[tuple[str, str], list[AccessRow]] | None = None
        self._lock = Lock()

    def run(
        self,
        region_id: str,
        municipality_id: str,
        criterion_id: str,
        threshold: float | None = None,
        deficit_only: bool = True,
        offset: int = 0,
        limit: int = 100,
    ) -> MunicipalAccessResult:
        if criterion_id not in SCENARIO_THRESHOLDS:
            raise InvalidQuery("Unknown accessibility criterion")
        policy = scenario_policy(criterion_id)
        threshold = policy.thresholds[0] if threshold is None else threshold
        if not isfinite(threshold) or threshold <= 0 or offset < 0 or not 1 <= limit <= 1000:
            raise InvalidQuery("Invalid threshold or pagination")
        municipality = next(
            (item for item in self.municipalities.run(region_id).items if item.id == municipality_id),
            None,
        )
        if municipality is None:
            raise InvalidQuery("Municipality does not belong to the region")
        snapshot = self.snapshot(municipality, criterion_id)
        if snapshot is None:
            raise DataUnavailable("Published municipal measurements are unavailable or stale")
        metadata = json.loads(snapshot.source.metadata_json)
        if (snapshot.source.region_id != region_id or snapshot.source.criterion_id != criterion_id
                or snapshot.source.stage != "scenario" or metadata.get("mode") != policy.mode
                or metadata.get("unit") != policy.unit or metadata.get("unavailable_reason")):
            raise DataUnavailable("Published measurement does not match the requested policy")
        rows = self.selected_rows(snapshot, municipality)

        def cost(row: AccessRow) -> float | None:
            value = row.distance_metres if policy.unit == "metres" else row.minutes
            return value if value is not None and isfinite(value) and value >= 0 and row.state != "unreachable" else None

        def deficit(row: AccessRow) -> bool:
            value = cost(row)
            return row.state == "unreachable" or (value is not None and value > threshold)

        finite = sorted(value for row in rows if (value := cost(row)) is not None)
        unreachable = sum(row.state == "unreachable" for row in rows)
        ordered = sorted(
            (row for row in rows if not deficit_only or deficit(row)),
            key=lambda row: (
                0 if row.state == "unreachable" else 1 if cost(row) is not None else 2,
                -(cost(row) or 0), row.id,
            ),
        )
        page = ordered[offset:offset + limit]
        facilities = {item.id: item for item in self.facilities(
            snapshot.source.run_id, {row.facility_id for row in page if row.facility_id}
        )}
        worst = finite[-ceil(len(finite) / 10):] if finite else []
        return MunicipalAccessResult(
            region_id, municipality_id, criterion_id, snapshot.sha256, snapshot.source.run_id,
            snapshot.source.measured_at, policy.unit, policy.mode, threshold, len(rows), len(finite),
            unreachable, len(rows) - len(finite) - unreachable, sum(deficit(row) for row in rows),
            finite[ceil(.9 * len(finite)) - 1] if finite else None,
            sum(worst) / len(worst) if worst else None,
            [MunicipalAccessPoint(row, facilities.get(row.facility_id or ""), deficit(row)) for row in page],
            len(ordered), offset, limit,
        )

    def selected_rows(self, snapshot: MunicipalAccessSnapshot, municipality: Municipality) -> list[AccessRow]:
        key = (snapshot.sha256, municipal_boundary_digest([municipality]))
        with self._lock:
            if self._selection is not None and self._selection[0] == key:
                return self._selection[1]
        vertices = [point for polygon in municipality.coordinates for ring in polygon for point in ring]
        if not vertices:
            return []
        west, east = min(p[0] for p in vertices), max(p[0] for p in vertices)
        south, north = min(p[1] for p in vertices), max(p[1] for p in vertices)
        rows = [row for row in snapshot.rows if row.longitude is not None
                and row.latitude is not None and south <= row.latitude <= north
                and any(west <= row.longitude + shift <= east for shift in (-360, 0, 360))
                and municipal_contains(row.longitude, row.latitude, municipality.coordinates)]
        with self._lock:
            self._selection = (key, rows)
        return rows
