import time

import numpy as np
from scipy.ndimage import label
from scipy.sparse.csgraph import connected_components
from synthetic_traffic.alignment import route_with_retries
from synthetic_traffic.alignment_validation import record_alignment_attempt
from synthetic_traffic.assignment import route_graph
from synthetic_traffic.candidate_targets import rank_targets
from synthetic_traffic.capacity_clearance import screen_capacity
from synthetic_traffic.corridor import find_corridor
from synthetic_traffic.geography import RasterGeography
from synthetic_traffic.model import Network
from synthetic_traffic.projects import apply_project, connection_design


def generate_candidates(
    network: Network,
    flow: np.ndarray,
    hours: np.ndarray,
    ratio: np.ndarray,
    limit: int = 20,
    geography=None,
    deadline=None,
    *,
    trips=None,
    zones=None,
    hypotheses=None,
    check=None,
) -> dict:
    if limit < 1 or any(len(v) != len(network.source) for v in [flow, hours, ratio]):
        raise ValueError(
            "Candidate inputs must match the network and use a positive limit"
        )
    if any(np.any(~np.isfinite(v)) or np.any(v < 0) for v in [flow, hours, ratio]):
        raise ValueError("Candidate flow/time inputs must be finite and nonnegative")
    if check:
        check()
    surface = None
    if geography is not None:
        surface = (
            geography
            if isinstance(geography, RasterGeography)
            else RasterGeography.load(
                geography,
                bounds=[
                    float(network.lon.min()),
                    float(network.lat.min()),
                    float(network.lon.max()),
                    float(network.lat.max()),
                ],
            )
        )
    if hypotheses and surface is None:
        raise ValueError("Corridor hypotheses require sourced geographic coverage")
    capacity_checked = capacity_rejected = 0
    roads = []
    seen = set()
    priority = flow * (hours + np.maximum(hours - network.free_hours, 0))
    for edge in np.argsort(-priority, kind="stable"):
        if check:
            check()
        if deadline is not None and time.monotonic() >= deadline:
            break
        if flow[edge] <= 0:
            continue
        way = int(network.way_id[edge])
        if way in seen or way < 0:
            continue
        seen.add(way)
        for project in (
            {"kind": "capacity", "way_ids": [way], "extra_lanes": lanes}
            for lanes in (1, 2)
        ):
            try:
                apply_project(network, project)
            except ValueError:
                continue
            capacity_checked += 1
            clearance = screen_capacity(network, project, surface)
            if clearance is None:
                capacity_rejected += 1
                continue
            roads.append(
                {
                    **project,
                    **clearance,
                    "feasibility_status": "raster_screened",
                    "screening_only": True,
                    "current_edge_demand_capacity_ratio": float(ratio[edge]),
                }
            )
        project = {"kind": "closure", "way_ids": [way]}
        try:
            apply_project(network, project)
        except ValueError:
            pass
        else:
            roads.append({**project, "screening_only": True})
        if len(seen) >= limit:
            break
    result = {
        "existing_corridor_projects": roads,
        "connections_for_review": [],
        "data_gaps": [],
        "geography_status": "unavailable",
        "capacity_screening": {
            "status": "raster_screened" if surface is not None else "missing_geography",
            "checked": capacity_checked,
            "rejected": capacity_rejected,
            "gap": None
            if surface is not None
            else "Widening requires sourced raster coverage of its full buffered alignment",
        },
    }
    if geography is None:
        result["geography_missing"] = ["elevation", "water", "buildings", "protected"]
        return result
    result["geography_status"] = "prepared_raster"
    for opening in surface.openings:
        project = {**opening, "kind": "opening", "screening_only": True}
        if not project.get("geometry"):
            raise ValueError("Sourced road openings need their actual alignment")
        apply_project(network, project)
        roads.append(project)
    graph, _ = route_graph(network, hours)
    _, components = connected_components(graph, directed=True, connection="strong")
    if network.access_raw_nodes is not None:
        positions = np.searchsorted(network.raw_nodes, network.access_raw_nodes)
        valid = positions < len(network.raw_nodes)
        access = positions[valid]
        access = access[network.raw_nodes[access] == network.access_raw_nodes[valid]]
    else:
        access = np.arange(len(network.raw_nodes))
    access = np.asarray(
        [
            node
            for node in access
            if (
                cell := surface.cell(float(network.lon[node]), float(network.lat[node]))
            )
            is not None
            and not surface.blocked[cell]
        ],
        dtype=int,
    )
    raster_components, _ = label(~surface.blocked)
    geography_groups = {
        int(node): int(
            raster_components[
                surface.cell(float(network.lon[node]), float(network.lat[node]))
            ]
        )
        for node in access
    }
    diagnostics = {}
    targets = rank_targets(
        network,
        hours,
        access,
        components,
        flow=flow,
        trips=trips,
        zones=zones,
        hypotheses=hypotheses,
        geography_groups=geography_groups,
        deadline=deadline,
        check=check,
        limit=min(512, max(128, limit * 4)),
        diagnostics=diagnostics,
    )
    result["target_diagnostics"] = diagnostics
    result["target_proposals"] = [
        {
            **{
                key: value
                for key, value in target.items()
                if key not in {"source_index", "target_index"}
            },
            "source_node": int(network.raw_nodes[target["source_index"]]),
            "target_node": int(network.raw_nodes[target["target_index"]]),
        }
        for target in targets[:128]
    ]
    result["target_count"] = len(targets)
    result["target_method"] = "fixed_od_detour_population_gap_and_validated_hypotheses"
    penalties = {}
    attempts = {}
    for _ in range(3):
        for target in targets:
            if check:
                check()
            if deadline is not None and time.monotonic() >= deadline:
                return result
            a, b = target["source_index"], target["target_index"]
            pair = a, b
            if attempts.get(pair, 0) >= 3:
                continue
            start = [float(network.lon[a]), float(network.lat[a])]
            finish = [float(network.lon[b]), float(network.lat[b])]
            penalty = penalties.setdefault(pair, {})
            try:
                route, design, used, rejected = route_with_retries(
                    surface,
                    start,
                    finish,
                    deadline,
                    penalty,
                    3 - attempts.get(pair, 0),
                    find_corridor,
                    connection_design,
                    check,
                )
            except TimeoutError:
                return result
            attempts[pair] = attempts.get(pair, 0) + used
            record_alignment_attempt(result, rejected, used)
            if route is None:
                attempts[pair] = 3
                continue
            if any(
                item["geometry"] == design["geometry"]
                for item in result["connections_for_review"]
            ):
                continue
            metadata = {
                key: value
                for key, value in target.items()
                if key not in {"source_index", "target_index"}
            }
            project = {
                **route,
                **metadata,
                "kind": "connection",
                "source_node": int(network.raw_nodes[a]),
                "target_node": int(network.raw_nodes[b]),
                **design,
                "screening_only": True,
                "alignment_variant": attempts[pair],
                "assumed_new_link_minutes": design["free_travel_hours"] * 60,
            }
            apply_project(network, project)
            if target["disconnected"]:
                result["data_gaps"].append(
                    {**project, "review": "verify_source_connectivity_before_building"}
                )
            result["connections_for_review"].append(project)
            if len(result["connections_for_review"]) >= min(128, limit):
                return result
    return result
