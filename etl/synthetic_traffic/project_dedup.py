import json
from itertools import groupby
from math import isfinite

import numpy as np
from synthetic_traffic.geography import polyline_km


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def independent(projects, network=None):
    parts = [
        part
        for project in projects
        for part in (
            project.get("projects", [])
            if project.get("kind") == "package"
            else [project]
        )
    ]
    if any(part.get("kind") == "package" for part in parts):
        return False
    ways, pairs, closed, additions = set(), set(), set(), False
    for part in parts:
        current = set(part.get("way_ids", []))
        if ways & current or any(
            not isinstance(way, int) or way < 0 for way in current
        ):
            return False
        ways |= current
        if part.get("kind") == "closure":
            closed |= current
        if part.get("kind") in {"connection", "opening"}:
            additions = True
            pair = tuple(sorted((part["source_node"], part["target_node"])))
            if pair in pairs:
                return False
            pairs.add(pair)
    return not (
        closed
        and additions
        and (network is None or set(map(int, network.way_id)) <= closed)
    )


def physical_key(project, network=None):
    try:
        kind = project["kind"]
        if kind == "package":
            if not independent(project["projects"], network):
                return None
            keys = [physical_key(part, network) for part in project["projects"]]
            if not keys or any(key is None for key in keys):
                return None
            return (
                ("package", tuple(sorted(keys, key=repr)))
            )
        if kind in {"capacity", "closure"}:
            ways = project["way_ids"]
            if not ways or any(
                isinstance(w, bool) or not isinstance(w, int) for w in ways
            ):
                return None
            lanes = project.get("extra_lanes", 1) if kind == "capacity" else 0
            if (
                isinstance(lanes, bool)
                or not isinstance(lanes, int)
                or not 0 <= lanes <= 5
            ):
                return None
            return kind, tuple(sorted(set(ways))), lanes
        if kind not in {"connection", "opening"}:
            return None
        source, target = project["source_node"], project["target_node"]
        if (
            any(isinstance(v, bool) or not isinstance(v, int) for v in (source, target))
            or source == target
        ):
            return None
        if kind == "opening" and not project.get("source_reference"):
            return None
        geometry = project["geometry"]
        if geometry["type"] != "LineString":
            return None
        coordinates = tuple(
            tuple(map(float, point)) for point in geometry["coordinates"]
        )
        if len(coordinates) < 2 or any(
            len(point) != 2 or not all(map(isfinite, point)) for point in coordinates
        ):
            return None
        measured = polyline_km(geometry["coordinates"])
        if not np.isclose(project["length_km"], measured, rtol=0.005, atol=0.001):
            return None
        coordinates = tuple(point for point, _ in groupby(coordinates))
        if source > target:
            source, target, coordinates = target, source, coordinates[::-1]
        speed, capacity = (
            float(project.get("speed_kmh", 40)),
            float(project.get("capacity_vph", 1800)),
        )
        if (
            not isfinite(speed)
            or not 0 < speed <= 140
            or not isfinite(capacity)
            or capacity <= 0
        ):
            return None
        semantics = {
            key: project[key]
            for key in (
                "road_class",
                "lanes_per_direction",
                "surface",
                "geography_sources",
                "source_reference",
                "oneway",
                "bidirectional",
                "direction",
            )
            if key in project
        }
        semantics["structures"] = sorted(project.get("structures", []), key=_json)
        return (
            kind,
            source,
            target,
            coordinates,
            measured,
            speed,
            capacity,
            _json(semantics),
        )
    except (KeyError, TypeError, ValueError, OverflowError):
        return None


def _canonical(project, network=None):
    result = dict(project)
    if project.get("kind") == "package" and physical_key(project, network) is not None:
        result["projects"] = sorted(
            (_canonical(part, network) for part in project["projects"]),
            key=lambda part: repr(physical_key(part, network)),
        )
    return result


def _records(project):
    return project.get("equivalent_proposals", [project])


def _sources(project):
    if project.get("source_provenance"):
        return project["source_provenance"]
    keys = (
        "target_origin",
        "target_rationale",
        "hypothesis_reason",
        "original_source_node",
        "original_target_node",
        "source_snap_road_km",
        "target_snap_road_km",
        "source_place",
        "target_place",
        "target_reason",
    )
    result = {key: project[key] for key in keys if key in project}
    result.setdefault(
        "target_origin",
        project.get(
            "origin",
            "automatic_connection"
            if project.get("kind") == "connection"
            else "existing_corridor",
        ),
    )
    return [result]


def _unique(records):
    return list({_json(record): record for record in records}.values())


def _merge(left, right, network=None):
    result = dict(left)
    records = _unique([*_records(left), *_records(right)])
    result["equivalent_proposals"] = records
    result["source_provenance"] = _unique(
        [source for record in records for source in _sources(record)]
    )
    if left.get("kind") == right.get("kind") == "package":
        result["projects"] = [
            _merge(a, b, network)
            for a, b in zip(left["projects"], right["projects"], strict=True)
        ]
    return result


def deduplicate_projects(projects, network=None):
    result, positions, removed = [], {}, 0
    for project in projects:
        key = physical_key(project, network)
        if key is not None and key in positions:
            index = positions[key]
            result[index] = _merge(result[index], _canonical(project, network), network)
            removed += 1
        else:
            if key is not None:
                positions[key] = len(result)
            result.append(_canonical(project, network))
    return result, removed
