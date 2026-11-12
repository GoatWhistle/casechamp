from typing import Any

import numpy as np
from synthetic_traffic.assignment import Assignment
from synthetic_traffic.model import Network
from synthetic_traffic.search import SearchResult

from app.adapter.traffic.indices import TrafficIndices
from app.adapter.traffic.visuals import metrics, roads
from app.usecase.traffic import TrafficAlternative, TrafficIndexChange, TrafficIndexValue


def parts(project: dict[str, Any]) -> list[dict[str, Any]]:
    return project["projects"] if project["kind"] == "package" else [project]


def proposal(
    identifier: str,
    result: SearchResult,
    original: Network,
    before: Assignment,
    baseline_indices: list[TrafficIndexValue],
    after_indices: list[TrafficIndexValue],
    indices: TrafficIndices | None,
) -> TrafficAlternative:
    project, changed, after = result.project, result.network, result.after
    children = parts(project)
    ways = sorted({way for part in children for way in part.get("way_ids", [])})
    length = sum(float(part.get("length_km", 0)) for part in children)
    selected = np.flatnonzero(np.isin(original.way_id, ways))
    pairs = {
        (
            int(original.way_id[i]),
            min(int(original.source[i]), int(original.target[i])),
            max(int(original.source[i]), int(original.target[i])),
        ): float(original.length_km[i])
        for i in selected
    }
    length += sum(pairs.values())
    base = {value.region: value for value in baseline_indices}
    changes = [
        TrafficIndexChange(
            value.region,
            base[value.region].value,
            value.value,
            value.value - base[value.region].value,
            (value.value / base[value.region].value - 1) * 100
            if base[value.region].value
            else None,
            value.population,
        )
        for value in after_indices
    ]
    comparable = all(
        (a is None) == (b is None) for a, b in zip(before.od_hours, after.od_hours, strict=True)
    )
    saving = before.vehicle_hours_per_hour - after.vehicle_hours_per_hour if comparable else None
    geometry = roads(changed, before, after, ways, len(original.source), original=original)
    new_projects = [p for p in children if p["kind"] in {"connection", "opening"}]
    for part, way in zip(
        new_projects, sorted({r.way_id for r in geometry if r.new_link}, reverse=True)
    ):
        coordinates = part.get("geometry", {}).get("coordinates")
        if coordinates:
            for position, row in enumerate(geometry):
                if row.new_link and row.way_id == way:
                    oriented = (
                        coordinates
                        if row.coordinates[0] == coordinates[0]
                        else list(reversed(coordinates))
                    )
                    geometry[position] = type(row)(
                        row.way_id,
                        oriented,
                        row.flow_before,
                        row.flow_after,
                        row.ratio_before,
                        row.ratio_after,
                        row.project,
                        row.new_link,
                    )
    closed = {w for p in children if p["kind"] == "closure" for w in p.get("way_ids", [])}
    if closed:
        for row in roads(original, before, before, sorted(closed), len(original.source)):
            if row.way_id in closed:
                geometry.append(
                    type(row)(
                        row.way_id,
                        row.coordinates,
                        row.flow_before,
                        0,
                        row.ratio_before,
                        0,
                        True,
                        False,
                    )
                )
    return TrafficAlternative(
        identifier,
        project["kind"],
        ways,
        length,
        saving,
        metrics(after),
        geometry,
        changes,
        road_names=indices.names(ways) if indices and ways else [],
        housing_clearance=all(
            p.get("geography_sources") for p in children if p["kind"] == "connection"
        )
        or None,
        structures=[s for p in children for s in p.get("structures", [])],
        overload_increase=int((after.ratio > 1).sum()) - int((before.ratio > 1).sum()),
    )
