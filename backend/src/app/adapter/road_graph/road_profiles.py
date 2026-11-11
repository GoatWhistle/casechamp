from dataclasses import replace
from typing import Any

from app.adapter.road_graph.data import GraphData
from app.domain.errors import InvalidQuery
from app.domain.road_cost import evaluate_road
from app.usecase.road_profile_validation import has_profile
from app.usecase.road_records import RoadChange


def profile_changes(
    changes: list[RoadChange],
    indices: dict[int, int],
    profiles: dict[int, dict[str, Any]],
) -> tuple[list[RoadChange], list[str]]:
    result = []
    notes = set()
    for change in changes:
        if not has_profile(change):
            result.append(change)
            continue
        index = indices[change.way_id]
        if index not in profiles:
            raise InvalidQuery("Road cost profile is unavailable for the selected road")
        before = {**profiles[index], "length_km": 1.0}
        after = dict(before)
        for field in ["lanes_total", "highway", "surface"]:
            value = getattr(change, field)
            if value is not None:
                after[field] = value
        if change.lanes_total is not None:
            after["lane_data_usable"] = True
            after["lanes_forward"] = None
            after["lanes_backward"] = None
        if change.speed_kmh is not None:
            after["override_speed_kmh"] = change.speed_kmh
            after["posted_speed_kmh"] = change.speed_kmh
        old_cost, new_cost = evaluate_road(**before), evaluate_road(**after)
        if old_cost.travel_hours <= 0 or new_cost.travel_hours <= 0:
            raise InvalidQuery("Road profile requires a positive finite travel time")
        factor = old_cost.travel_hours / new_cost.travel_hours
        result.append(replace(change, speed_factor=factor))
        if not before.get("flow_verified") or before.get("hourly_flow_pcu") is None:
            notes.add("unverified_flow_free_flow")
            if change.lanes_total is not None:
                notes.add("lanes_without_verified_flow_no_time_effect")
        if old_cost.lane_basis in {
            "narrow_unknown_lanes_v1",
            "osm_partial_narrow_unknown_lanes_v1",
        }:
            notes.add("missing_lanes_default_one_per_direction")
    return result, sorted(notes)


def requested_profiles(
    data: GraphData, changes: list[RoadChange]
) -> dict[int, dict[str, Any]] | None:
    if not any(has_profile(change) for change in changes):
        return None
    return data.cost_profiles([change.way_id for change in changes])
