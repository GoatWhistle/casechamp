from dataclasses import dataclass
from math import isfinite
from typing import Literal

from app.domain.road_profiles import (
    CAPACITY_PER_LANE_PCU_H,
    SPEED_KMH,
    UNPAVED,
    UNPAVED_FACTOR,
    canonical_oneway,
    lane_profile,
    validate_lane_counts,
)

METHOD_VERSION = "road-capacity-v1"
BPR_ALPHA = 0.15
BPR_BETA = 4
type FlowScope = Literal["directional", "bidirectional_total"]


@dataclass(frozen=True)
class RoadCost:
    speed_kmh: float
    free_flow_hours: float
    travel_hours: float
    delay_hours: float
    lanes_total: int | None
    lanes_forward: int | None
    lanes_backward: int | None
    effective_lanes: int | None
    capacity_pcu_h: float | None
    flow_basis: Literal["unknown_free_flow", "confirmed", "not_applicable"]
    lane_basis: str
    capacity_basis: str
    flow_source: str
    flow_period: str
    shared_lane: bool
    flow_scope: FlowScope
    hourly_flow_pcu: float | None
    method_version: str = METHOD_VERSION


def finite_value(value: float, name: str, *, positive: bool = False) -> None:
    if isinstance(value, bool) or not isfinite(value) or value < 0 or (positive and value == 0):
        raise ValueError(f"{name} must be finite and {'positive' if positive else 'nonnegative'}")


def evaluate_road(
    *,
    length_km: float,
    highway: str,
    surface: str | None = None,
    lanes_total: int | None = None,
    lanes_forward: int | None = None,
    lanes_backward: int | None = None,
    oneway: str | None = None,
    posted_speed_kmh: float | None = None,
    hourly_flow_pcu: float | None = None,
    flow_verified: bool = False,
    flow_source: str = "",
    flow_period: str = "",
    hourly_flow_scope: FlowScope = "directional",
    is_ferry: bool = False,
    source_speed_kmh: float | None = None,
    override_speed_kmh: float | None = None,
    lane_data_usable: bool = True,
) -> RoadCost:
    finite_value(length_km, "length_km")
    validate_lane_counts(lanes_total, lanes_forward, lanes_backward)
    for name, value in [
        ("posted_speed_kmh", posted_speed_kmh),
        ("source_speed_kmh", source_speed_kmh),
        ("override_speed_kmh", override_speed_kmh),
    ]:
        if value is not None:
            finite_value(value, name, positive=True)
    if hourly_flow_pcu is not None:
        finite_value(hourly_flow_pcu, "hourly_flow_pcu")
    if hourly_flow_scope not in {"directional", "bidirectional_total"}:
        raise ValueError("Unsupported hourly flow scope")
    if is_ferry or highway == "ferry":
        speed = source_speed_kmh if source_speed_kmh is not None else 10.0
        hours = length_km / speed
        return RoadCost(
            speed,
            hours,
            hours,
            0.0,
            None,
            None,
            None,
            None,
            None,
            "not_applicable",
            "not_applicable",
            "not_applicable",
            "",
            "",
            False,
            hourly_flow_scope,
            None,
        )
    road_class = highway.removesuffix("_link")
    speed = SPEED_KMH.get(road_class, source_speed_kmh if source_speed_kmh is not None else 30.0)
    if override_speed_kmh is not None:
        speed = override_speed_kmh
    elif surface in UNPAVED or (road_class == "track" and not surface):
        speed *= UNPAVED_FACTOR
    if posted_speed_kmh is not None:
        speed = min(speed, posted_speed_kmh)
    free = length_km / speed
    confirmed = hourly_flow_pcu is not None and flow_verified
    if confirmed and (not flow_source.strip() or not flow_period.strip()):
        raise ValueError("Confirmed hourly flow requires a source and observation period")
    mode = canonical_oneway(oneway)
    if not lane_data_usable or mode not in {"forward", "reverse", "bidirectional", "unknown"}:
        if confirmed:
            raise ValueError("Confirmed flow requires resolved lane metadata and operating mode")
        return RoadCost(
            speed,
            free,
            free,
            0.0,
            lanes_total,
            lanes_forward,
            lanes_backward,
            None,
            None,
            "unknown_free_flow",
            "unresolved",
            "unresolved_lane_metadata_v1",
            flow_source,
            flow_period,
            False,
            hourly_flow_scope,
            hourly_flow_pcu,
        )
    lanes = lane_profile(lanes_total, lanes_forward, lanes_backward, mode)
    capacity = lanes.effective * CAPACITY_PER_LANE_PCU_H
    if confirmed and (lanes.shared != (hourly_flow_scope == "bidirectional_total")):
        raise ValueError("Hourly flow scope does not match representative lane capacity")
    travel = free
    if confirmed:
        assert hourly_flow_pcu is not None
        try:
            travel *= 1.0 + BPR_ALPHA * (hourly_flow_pcu / capacity) ** BPR_BETA
        except OverflowError as error:
            raise ValueError("Loaded travel time exceeds finite model range") from error
        if not isfinite(travel):
            raise ValueError("Loaded travel time exceeds finite model range")
    capacity_basis = "uncalibrated_uniform_1800_pcu_per_lane_v1"
    if lanes.shared:
        capacity_basis = "uncalibrated_shared_lane_1800_pcu_total_v1"
    return RoadCost(
        speed,
        free,
        travel,
        travel - free,
        lanes.total,
        lanes.forward,
        lanes.backward,
        lanes.effective,
        capacity,
        "confirmed" if confirmed else "unknown_free_flow",
        lanes.basis,
        capacity_basis,
        flow_source,
        flow_period,
        lanes.shared,
        hourly_flow_scope,
        hourly_flow_pcu,
    )
