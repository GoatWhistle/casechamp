from dataclasses import replace
from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.parquet as pq
from scipy.spatial import cKDTree
from synthetic_traffic.demand import xyz
from synthetic_traffic.model import Zone

from app.domain.errors import InvalidQuery
from app.usecase.traffic import TrafficJob


def resolve_focus(
    job: TrafficJob, path: Path, settlements: list[Zone], homes: list[Zone]
) -> tuple[TrafficJob, dict[str, Any]]:
    if job.scope.objective == "connectivity" or job.scope.focus_bounds:
        return job, {"basis": "explicit_bounds" if job.scope.focus_bounds else "context"}
    if len(job.scope.places) != 1:
        return job, {"basis": "context"}
    name = job.scope.places[0].casefold()
    rows = pq.read_table(path / "places.parquet").to_pylist()
    identifiers = {
        str(row["point_id"])
        for row in rows
        if name in {str(row["point_id"]).casefold(), str(row["settlement"]).casefold()}
        and (not job.scope.region or str(row["region"]).casefold() == job.scope.region.casefold())
    }
    if len(identifiers) != 1:
        raise InvalidQuery("Focus settlement is missing or ambiguous")
    identifier = identifiers.pop()
    locations = xyz(np.array([z.lat for z in settlements]), np.array([z.lon for z in settlements]))
    houses = [h for h in homes if h.id.startswith("home-")]
    if not houses:
        raise InvalidQuery("No residential envelope for this settlement; supply focus_bounds")
    distance, nearest = cKDTree(locations).query(
        xyz(np.array([h.lat for h in houses]), np.array([h.lon for h in houses]))
    )
    selected = [
        h
        for h, d, index in zip(houses, distance, nearest, strict=True)
        if d <= 5 and settlements[int(index)].id == identifier
    ]
    if not selected:
        raise InvalidQuery("No residential envelope for this settlement; supply focus_bounds")
    latitude = max(abs(h.lat) for h in selected)
    margin = 0.1 / (111 * max(0.1, float(np.cos(np.radians(latitude)))))
    bounds = [
        min(h.lon for h in selected) - margin,
        min(h.lat for h in selected) - 0.1 / 111,
        max(h.lon for h in selected) + margin,
        max(h.lat for h in selected) + 0.1 / 111,
    ]
    return replace(job, scope=replace(job.scope, focus_bounds=bounds)), {
        "basis": "allocated_residential_envelope",
        "settlement_id": identifier,
        "buildings": len(selected),
        "assignment_radius_km": 5,
        "padding_km": 0.1,
        "administrative_boundary": False,
        "bounds": bounds,
    }
