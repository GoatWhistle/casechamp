import re
from dataclasses import dataclass, fields
from datetime import datetime
from math import isfinite
from typing import get_args


@dataclass(frozen=True, slots=True, kw_only=True)
class WalkingFacts:
    origin_id: str
    service: str
    source_url: str
    observed_at: str
    population: int | None = None
    population_group: str | None = None
    population_group_verified: bool = False
    facility_id: str | None = None
    eligible_facility_ids: tuple[str, ...] = ()
    eligible_inventory_complete: bool = False
    scenario_verified: bool = False
    verified_closed_way_ids: tuple[int, ...] = ()
    entrance_latitude: float | None = None
    entrance_longitude: float | None = None
    entrance_verified: bool = False
    facts_verified: bool = False
    legal_currentness_verified: bool = False
    measurement_verified: bool = False
    measurement_graph_revision: str | None = None
    service_eligible: bool | None = None
    service_active: bool | None = None
    region_code: str | None = None
    municipality_type: str | None = None
    municipality_legal_id: str | None = None
    settlement_legal_id: str | None = None
    settlement_category: str | None = None
    origin_kind: str | None = None
    exception_800_applicable: bool | None = None
    exception_source_url: str | None = None
    sanitary_project_case: str | None = None
    regional_planning_scope: bool | None = None
    municipal_planning_scope: bool | None = None
    zones: tuple[str, ...] = ()
    zone_source_url: str | None = None
    zone_version: str | None = None
    zoning_complete: bool | None = None
    bus_scope: bool | None = None
    bus_active: bool | None = None
    bus_return_trip: bool | None = None
    bus_vehicle_verified: bool = False
    bus_route_km: float | None = None
    bus_approach_metres: float | None = None
    regional_transport_km: float | None = None

    def __post_init__(self) -> None:
        allowed = {
            "service": {"school", "stop"},
            "population_group": {"school_children", "residents"},
            "municipality_type": {"urban_okrug", "municipal_okrug"},
            "settlement_category": {"city", "urban_settlement", "rural"},
            "origin_kind": {
                "residential",
                "child_residential_institution",
                "industrial_gate",
                "recreation_entry",
            },
            "sanitary_project_case": {"current", "transitional_review"},
        }
        if not self.origin_id or not self.source_url or not self.observed_at:
            raise ValueError("Walking facts require an origin and dated source")
        for key, values in allowed.items():
            value = getattr(self, key)
            if value is not None and value not in values:
                raise ValueError(f"Invalid walking fact: {key}")
        if (
            not isinstance(self.eligible_facility_ids, tuple)
            or any(not isinstance(key, str) or not key for key in self.eligible_facility_ids)
            or len(set(self.eligible_facility_ids)) != len(self.eligible_facility_ids)
        ):
            raise ValueError("Eligible facility identifiers must be a unique tuple")
        if (
            not isinstance(self.verified_closed_way_ids, tuple)
            or any(type(key) is not int or key <= 0 for key in self.verified_closed_way_ids)
            or len(set(self.verified_closed_way_ids)) != len(self.verified_closed_way_ids)
            or len(self.verified_closed_way_ids) > 20
        ):
            raise ValueError("Verified closure identifiers must be unique positive integers")
        if len(set(self.zones)) != len(self.zones) or set(self.zones) - {
            "city_centre",
            "industrial",
            "recreation",
            "individual_housing",
            "other",
        }:
            raise ValueError("Invalid walking zones")
        if self.population is not None and (
            type(self.population) is not int or self.population < 0
        ):
            raise ValueError("Population must be a nonnegative integer")
        if self.population_group_verified and (
            self.population is None
            or self.population_group
            != {"school": "school_children", "stop": "residents"}[self.service]
        ):
            raise ValueError("The verified population group must match the selected service")
        if self.entrance_verified and (
            self.entrance_latitude is None or self.entrance_longitude is None
        ):
            raise ValueError("A verified entrance requires coordinates")
        for value, limit in [(self.entrance_latitude, 90), (self.entrance_longitude, 180)]:
            if value is not None and (not isfinite(value) or abs(value) > limit):
                raise ValueError("Invalid entrance coordinates")
        for value, size in [
            (self.region_code, 2),
            (self.municipality_legal_id, 8),
            (self.settlement_legal_id, 11),
        ]:
            if value is not None and (
                not isinstance(value, str)
                or re.fullmatch(r"[0-9]{" + str(size) + "}", value) is None
            ):
                raise ValueError("Invalid jurisdiction identifier")
        datetime.fromisoformat(self.observed_at)
        for field in fields(self):
            value = getattr(self, field.name)
            args = get_args(field.type)
            kinds = args if type(None) in args else (field.type,)
            if value is not None and bool in kinds and type(value) is not bool:
                raise ValueError(f"Expected a boolean walking fact: {field.name}")
            if value is not None and str in kinds and type(value) is not str:
                raise ValueError(f"Expected a string walking fact: {field.name}")
            if (
                value is not None
                and float in kinds
                and (isinstance(value, bool) or not isinstance(value, (int, float)))
            ):
                raise ValueError(f"Expected a numeric walking fact: {field.name}")
            if (
                field.name in {"bus_route_km", "bus_approach_metres", "regional_transport_km"}
                and value is not None
                and (not isfinite(value) or value < 0)
            ):
                raise ValueError("Walking measurements must be finite and nonnegative")
