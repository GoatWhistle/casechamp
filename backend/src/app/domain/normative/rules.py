from dataclasses import dataclass
from math import isfinite
from typing import Literal

from app.domain.normative.model import AccessRow
from app.domain.normative.walking_facts import WalkingFacts

RuleId = Literal[
    "sp4283_school_walk",
    "rngp178_school_walk",
    "mngp114_school_walk",
    "sp4283_bus_approach",
    "sp4283_bus_route",
    "rngp178_school_transport",
    "rngp178_stop_walk",
    "mngp114_stop_walk",
]
RuleReason = Literal[
    "conditions_missing",
    "comparison_only",
    "facts_missing",
    "facts_unverified",
    "rule_currentness_unconfirmed",
    "target_mismatch",
    "measurement_unverified",
    "measurement_version_mismatch",
    "eligible_service_unconfirmed",
    "eligible_inventory_incomplete",
    "scenario_unverified",
    "school_transport_unconfirmed",
    "measurement_missing",
    "jurisdiction_unknown",
    "outside_jurisdiction",
    "planning_scope_unknown",
    "outside_planning_scope",
    "origin_profile_unknown",
    "settlement_unknown",
    "rural_branch",
    "exception_unknown",
    "exception_checked",
    "project_scope_unknown",
    "transitional_project_review",
    "institution_branch",
    "bus_scope_unknown",
    "outside_bus_scope",
    "bus_collection_point",
    "organized_transport_limit",
    "municipality_type_unknown",
    "no_numerical_limit",
    "municipal_okrug_transport",
    "municipal_rural_scope_review",
    "rural_not_regulated",
    "zone_unknown",
    "zone_conflict",
    "zoning_incomplete",
    "zone_selected",
    "settlement_id_unknown",
    "city_category_review",
    "kurgan_municipality_housing",
    "city_housing",
]
Applicability = Literal["unknown", "applicable", "not_applicable", "not_regulated"]
RuleUnit = Literal["metres", "kilometres"]
RuleResult = Literal["unknown", "within", "exceeded", "not_applicable", "not_regulated"]
SP = "http://publication.pravo.gov.ru/document/0001202606020083"
RNGP = "https://gkh.kurganobl.ru/?page_id=14474"
MNGP = "https://www.kurgan-city.ru/newclerk/-1/255692/"


@dataclass(frozen=True, slots=True)
class RuleSpec:
    source_url: str
    edition_date: str
    unit: RuleUnit
    measurement: str
    candidates: tuple[float, ...]


SPECS: dict[RuleId, RuleSpec] = {
    "sp4283_school_walk": RuleSpec(SP, "2026-06-02", "metres", "walking_path", (500, 800, 1000)),
    "rngp178_school_walk": RuleSpec(RNGP, "2023-02-08", "metres", "walking_path", (500, 800, 1000)),
    "mngp114_school_walk": RuleSpec(MNGP, "2023-10-18", "metres", "walking_path", (500, 800)),
    "sp4283_bus_approach": RuleSpec(SP, "2026-06-02", "metres", "bus_approach_metres", (500, 1000)),
    "sp4283_bus_route": RuleSpec(SP, "2026-06-02", "kilometres", "bus_route_km", (30,)),
    "rngp178_school_transport": RuleSpec(
        RNGP, "2023-02-08", "kilometres", "regional_transport_km", (15,)
    ),
    "rngp178_stop_walk": RuleSpec(
        RNGP, "2023-02-08", "metres", "walking_path", (250, 400, 500, 600, 800)
    ),
    "mngp114_stop_walk": RuleSpec(
        MNGP, "2023-10-18", "metres", "walking_path", (250, 400, 500, 600, 800)
    ),
}


@dataclass(frozen=True, slots=True)
class Choice:
    applicability: Applicability = "unknown"
    threshold: float | None = None
    reason: RuleReason = "conditions_missing"
    candidates: tuple[float, ...] | None = None


@dataclass(frozen=True, slots=True)
class RuleCheck:
    rule_id: RuleId
    applicability: Applicability
    threshold: float | None
    unit: RuleUnit
    measurement: str
    value: float | None
    result: RuleResult
    reason: RuleReason
    source_url: str
    edition_date: str
    facts_source_url: str | None
    facts_observed_at: str | None
    candidate_thresholds: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class RuleSet:
    id: str
    checks: tuple[RuleCheck, ...]


def assessed_rule(
    rule_id: RuleId, choice: Choice, row: AccessRow, facts: WalkingFacts | None
) -> RuleCheck:
    spec = SPECS[rule_id]
    value = (
        row.distance_metres
        if spec.measurement == "walking_path"
        else (getattr(facts, spec.measurement) if facts else None)
    )
    result: RuleResult = "unknown"
    reason = choice.reason
    if choice.applicability in {"not_applicable", "not_regulated"}:
        if facts is not None and facts.legal_currentness_verified:
            result = (
                "not_applicable" if choice.applicability == "not_applicable" else "not_regulated"
            )
        else:
            reason = "rule_currentness_unconfirmed"
    elif choice.applicability == "applicable" and facts:
        result, reason = compared(choice, value, row, facts, spec.measurement)
    return RuleCheck(
        rule_id,
        choice.applicability,
        float(choice.threshold) if choice.threshold is not None else None,
        spec.unit,
        spec.measurement,
        None if spec.measurement == "walking_path" or value is None else float(value),
        result,
        reason,
        spec.source_url,
        spec.edition_date,
        facts.source_url if facts else None,
        facts.observed_at if facts else None,
        tuple(
            float(candidate)
            for candidate in (
                choice.candidates
                if choice.candidates is not None
                else (spec.candidates if choice.applicability == "unknown" else ())
            )
        ),
    )


def compared(
    choice: Choice, value: float | None, row: AccessRow, facts: WalkingFacts, measurement: str
) -> tuple[RuleResult, RuleReason]:
    if not facts.facts_verified:
        return "unknown", "facts_unverified"
    if not facts.legal_currentness_verified:
        return "unknown", "rule_currentness_unconfirmed"
    eligible = facts.eligible_facility_ids or ((facts.facility_id,) if facts.facility_id else ())
    target_matches = (
        row.facility_id in eligible
        if measurement == "walking_path"
        else facts.facility_id == row.facility_id
    )
    if row.facility_id is None or not target_matches:
        return "unknown", "target_mismatch"
    if not facts.measurement_verified or any(
        reason in row.uncertainty
        for reason in (
            "residential_reference_not_entrance",
            "facility_entrances_unverified",
            "path_unconfirmed",
            "origin_unattached",
        )
    ):
        return "unknown", "measurement_unverified"
    if facts.service_eligible is not True or facts.service_active is not True:
        return "unknown", "eligible_service_unconfirmed"
    if measurement in {"bus_route_km", "bus_approach_metres"} and (
        facts.bus_active is not True
        or facts.bus_return_trip is not True
        or not facts.bus_vehicle_verified
    ):
        return "unknown", "school_transport_unconfirmed"
    if value is None or not isfinite(value) or value < 0:
        return "unknown", "measurement_missing"
    if choice.threshold is None:
        raise ValueError("An applicable numerical rule requires a threshold")
    if (
        value > choice.threshold
        and measurement == "walking_path"
        and not facts.eligible_inventory_complete
    ):
        return "unknown", "eligible_inventory_incomplete"
    return ("within" if value <= choice.threshold else "exceeded"), "comparison_only"


def available(facts: WalkingFacts | None) -> Choice | None:
    if facts is None:
        return Choice(reason="facts_missing")
    if not facts.facts_verified:
        return Choice(reason="facts_unverified")
    return None


def planning_scope(facts: WalkingFacts, municipal: bool) -> Choice | None:
    if facts.region_code is None:
        return Choice(reason="jurisdiction_unknown")
    if facts.region_code != "45":
        return Choice("not_applicable", reason="outside_jurisdiction")
    if municipal:
        if facts.municipality_legal_id is None:
            return Choice(reason="jurisdiction_unknown")
        if facts.municipality_legal_id != "37701000":
            return Choice("not_applicable", reason="outside_jurisdiction")
    scope = facts.municipal_planning_scope if municipal else facts.regional_planning_scope
    if scope is None:
        return Choice(reason="planning_scope_unknown")
    if scope is False:
        return Choice("not_applicable", reason="outside_planning_scope")
    return None
