import re
from dataclasses import dataclass
from typing import Literal

AccessState = Literal[
    "within", "exceeded", "unreachable", "unknown", "not_regulated", "not_applicable"
]
Uncertainty = Literal[
    "residential_reference_not_entrance",
    "population_group_missing",
    "territory_conditions_missing",
    "facility_entrances_unverified",
    "origin_unattached",
    "path_unconfirmed",
    "service_status_unconfirmed",
    "medical_catchment_unconfirmed",
    "transport_mode_unconfirmed",
    "facility_profile_unconfirmed",
    "fire_speed_assumed",
    "fire_vehicle_access_unconfirmed",
    "fire_readiness_unconfirmed",
    "fire_adverse_conditions_unconfirmed",
    "fire_directionality_unconfirmed",
    "fire_destination_unconfirmed",
    "fire_measurement_definition_unconfirmed",
    "qualification_unconfirmed",
    "evidence_outside_validity",
    "normative_rule_unconfirmed",
    "planning_scope_unconfirmed",
    "reference_location_unconfirmed",
    "measurement_version_unconfirmed",
    "scenario_conditions_unconfirmed",
    "inventory_incomplete",
    "ownership_scope_unconfirmed",
    "regional_adjustment_unconfirmed",
    "medical_form_unconfirmed",
    "adult_profile_unconfirmed",
]


@dataclass(frozen=True, slots=True)
class Criterion:
    id: str
    service: str
    act: str
    clause: str
    source_url: str
    edition_date: str
    threshold: float
    unit: str
    mode: str
    territory: str
    legal_status: str
    verification_status: str


@dataclass(frozen=True, slots=True)
class Facility:
    id: str
    service: str
    name: str
    address: str
    source_url: str
    observed_at: str
    latitude: float | None
    longitude: float | None
    coordinate_source: str | None
    coordinate_status: str
    published_on: str | None = None
    source_sha256: str | None = None
    coordinate_snapshot_sha256: str | None = None
    coordinate_snapshot_url: str | None = None

    def __post_init__(self) -> None:
        for digest in (self.source_sha256, self.coordinate_snapshot_sha256):
            if digest is not None and (
                not isinstance(digest, str) or re.fullmatch(r"[0-9a-f]{64}", digest) is None
            ):
                raise ValueError(
                    "Facility source SHA256 must contain 64 lowercase hexadecimal digits"
                )
        if (self.coordinate_snapshot_sha256 is None) != (self.coordinate_snapshot_url is None):
            raise ValueError("Coordinate snapshots require both their hash and source URL")
        if self.coordinate_snapshot_url is not None and (
            not isinstance(self.coordinate_snapshot_url, str)
            or not self.coordinate_snapshot_url.startswith(("https://", "http://"))
            or self.latitude is None
            or self.longitude is None
            or not self.coordinate_source
        ):
            raise ValueError("Coordinate snapshots require HTTP sources and known geometry")


@dataclass(frozen=True, slots=True)
class Origin:
    id: str
    name: str
    population: int | None
    node: int | None
    snap_km: float | None
    latitude: float | None
    longitude: float | None
    entrance_verified: bool = False


@dataclass(frozen=True, slots=True)
class AccessRow:
    id: str
    name: str
    population: int | None
    latitude: float | None
    longitude: float | None
    facility_id: str | None
    minutes: float | None
    excess_minutes: float | None
    state: AccessState
    distance_metres: float | None = None
    uncertainty: tuple[Uncertainty, ...] = ()
    routing_node: int | None = None
    approach_metres: float | None = None
    threshold_minutes: float | None = None
    territory_type: str | None = None
    territory_source_url: str | None = None
    rule_set_id: str | None = None
    territory_verification_status: str | None = None
    municipality_code: str | None = None
    territory_structure_source_url: str | None = None
    qualification_source_url: str | None = None
    qualification_observed_at: str | None = None
    catchment_source_url: str | None = None
    threshold_source_url: str | None = None
    travel_profile_source_url: str | None = None
    measurement_method_source_url: str | None = None
    origin_source_url: str | None = None
    origin_observed_at: str | None = None
    origin_source_sha256: str | None = None
    origin_reference_status: str | None = None


@dataclass(frozen=True, slots=True)
class Coverage:
    population: int
    within: int
    exceeded: int
    unreachable: int
    unknown: int
    unknown_population_points: int
    lower_percent: float | None
    upper_percent: float | None
    not_regulated_population: int = 0
    not_applicable_population: int = 0
    not_regulated_points: int = 0
    not_applicable_points: int = 0
    excluded_unknown_population_points: int = 0


def coverage(rows: list[AccessRow]) -> Coverage:
    if any(row.population is not None and row.population < 0 for row in rows):
        raise ValueError("Population cannot be negative")
    counts = {key: 0 for key in ("within", "exceeded", "unreachable", "unknown")}
    missing = 0
    excluded = {"not_regulated": 0, "not_applicable": 0}
    excluded_points = {key: 0 for key in excluded}
    excluded_missing = 0
    for row in rows:
        if row.state in excluded:
            excluded_points[row.state] += 1
            if row.population is None:
                excluded_missing += 1
            else:
                excluded[row.state] += row.population
        elif row.population is None:
            missing += 1
        else:
            counts[row.state] += row.population
    total = sum(counts.values())
    measurable = total > 0 and missing == 0
    lower = 100 * counts["within"] / total if measurable else None
    upper = 100 * (counts["within"] + counts["unknown"]) / total if measurable else None
    return Coverage(
        total,
        counts["within"],
        counts["exceeded"],
        counts["unreachable"],
        counts["unknown"],
        missing,
        lower,
        upper,
        excluded["not_regulated"],
        excluded["not_applicable"],
        excluded_points["not_regulated"],
        excluded_points["not_applicable"],
        excluded_missing,
    )
