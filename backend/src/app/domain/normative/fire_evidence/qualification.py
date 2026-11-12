from dataclasses import replace
from datetime import datetime
from math import isclose, isfinite

from app.domain.normative.fire import (
    FireProfile,
    SettlementContext,
    apply_fire_conditions,
    fire_threshold,
)
from app.domain.normative.fire_evidence.facts import FireFacts
from app.domain.normative.model import AccessRow, AccessState, Criterion, Facility, Uncertainty

EXITS = frozenset({"verified_fire_exit", "verified_fire_exit_complete_inventory"})


def apply_fire_evidence(
    criterion: Criterion,
    rows: list[AccessRow],
    settlements: list[SettlementContext],
    facts: list[FireFacts],
    facilities: list[Facility],
    graph_revision: str,
    instant: datetime | None,
    closed_way_ids: list[int],
    profile: FireProfile | None,
) -> list[AccessRow]:
    display = apply_fire_conditions(rows, settlements)
    if not facts:
        return display
    if instant is None or profile is None:
        raise ValueError("Fire evidence requires a decision time and an explicit travel profile")
    contexts = {fact.origin_id: fact for fact in facts}
    if len(contexts) != len(facts) or set(contexts) - {r.id for r in rows}:
        raise ValueError("Fire evidence has duplicate or unknown destinations")
    active = {key: f for key, f in contexts.items() if f.facts_verified and f.active_on(instant)}
    if len({f.population_reference for f in active.values() if f.population_verified}) > 1:
        raise ValueError("Fire population references cannot be mixed")
    targets = {f.id: f for f in facilities}
    territories = {s.point_id: s for s in settlements}
    result = []
    for raw, row in zip(rows, display, strict=True):
        fact = contexts.get(row.id)
        if active:
            current = active.get(row.id)
            population = current.population if current and current.population_verified else None
            row = replace(row, population=population)
            if population is None:
                row = replace(row, uncertainty=(*row.uncertainty, "population_group_missing"))
        if fact is None:
            result.append(row)
            continue
        row = replace(
            row,
            qualification_source_url=fact.source_url,
            qualification_observed_at=fact.observed_at,
        )
        reasons = list(row.uncertainty)
        if not fact.facts_verified:
            reasons.append("qualification_unconfirmed")
        elif not fact.active_on(instant):
            reasons.append("evidence_outside_validity")
        else:
            previous = territories.get(row.id)
            if fact.settlement_type_verified:
                if (
                    previous
                    and previous.verification_status == "primary_verified"
                    and previous.settlement_type != fact.settlement_type
                ):
                    raise ValueError("Conflicting verified fire settlement categories")
                row = replace(
                    row,
                    threshold_minutes=fire_threshold(fact.settlement_type),
                    territory_type=fact.settlement_type,
                    territory_source_url=fact.source_url,
                    territory_verification_status="verified_fire_settlement",
                )
                reasons = [r for r in reasons if r != "territory_conditions_missing"]
            confirmed: set[Uncertainty] = set()
            if (
                fact.speed_verified
                and fact.adverse_conditions_verified
                and fact.speed_kmh == profile.speed_kmh
                and fact.profile_assumption == profile.assumption
            ):
                confirmed.add("fire_speed_assumed")
            if fact.vehicle_access_verified:
                confirmed.add("fire_vehicle_access_unconfirmed")
            if fact.operational_readiness_verified:
                confirmed.add("fire_readiness_unconfirmed")
            if fact.eligible_facility_ids and all(
                key in targets and targets[key].coordinate_status in EXITS
                for key in fact.eligible_facility_ids
            ):
                confirmed.add("facility_entrances_unverified")
            reasons = [r for r in reasons if r not in confirmed]
            state, reason = qualified_state(
                criterion, raw, fact, targets, graph_revision, closed_way_ids, profile
            )
            if reason:
                reasons.append(reason)
            row = replace(
                row,
                state=state,
                travel_profile_source_url=fact.speed_source_url,
                measurement_method_source_url=fact.method_source_url,
                excess_minutes=max(0.0, raw.minutes - row.threshold_minutes)
                if state in {"within", "exceeded"}
                and raw.minutes is not None
                and row.threshold_minutes is not None
                else None,
            )
        result.append(replace(row, uncertainty=tuple(dict.fromkeys(reasons))))
    return result


def qualified_state(
    criterion: Criterion,
    row: AccessRow,
    fact: FireFacts,
    targets: dict[str, Facility],
    graph_revision: str,
    closed_way_ids: list[int],
    profile: FireProfile,
) -> tuple[AccessState, Uncertainty | None]:
    if (
        not fact.legal_currentness_verified
        or not fact.method_currentness_verified
        or fact.normative_source_url != criterion.source_url
        or fact.legal_edition_date != criterion.edition_date
    ):
        return "unknown", "normative_rule_unconfirmed"
    if not fact.jurisdiction_verified:
        return "unknown", "territory_conditions_missing"
    if fact.territory != criterion.territory or fact.planning_scope is False:
        return "not_applicable", None
    if fact.planning_scope is not True:
        return "unknown", "planning_scope_unconfirmed"
    if not fact.settlement_type_verified or fire_threshold(fact.settlement_type) is None:
        return "unknown", "territory_conditions_missing"
    if row.origin_reference_status is not None and row.origin_reference_status != "verified_object":
        return "unknown", "fire_destination_unconfirmed"
    if not fact.transport_method_verified or fact.transport_mode != "emergency_response":
        return "unknown", "transport_mode_unconfirmed"
    if (
        not fact.speed_verified
        or fact.speed_kmh is None
        or fact.speed_kmh != profile.speed_kmh
        or fact.profile_assumption != profile.assumption
    ):
        return "unknown", "fire_speed_assumed"
    checks: list[tuple[bool, Uncertainty]] = [
        (fact.adverse_conditions_verified, "fire_adverse_conditions_unconfirmed"),
        (fact.vehicle_access_verified, "fire_vehicle_access_unconfirmed"),
        (fact.directionality_verified, "fire_directionality_unconfirmed"),
        (fact.operational_readiness_verified, "fire_readiness_unconfirmed"),
        (fact.destination_objects_verified, "fire_destination_unconfirmed"),
        (
            fact.measurement_definition_verified
            and fact.measurement_definition == "depot_to_object_travel",
            "fire_measurement_definition_unconfirmed",
        ),
        (fact.service_eligible is True, "facility_profile_unconfirmed"),
        (fact.service_active is True, "service_status_unconfirmed"),
    ]
    for verified, reason in checks:
        if not verified:
            return "unknown", reason
    pairs = [
        (row.latitude, fact.origin_latitude),
        (row.longitude, fact.origin_longitude),
        (row.approach_metres, fact.approach_metres),
    ]
    if (
        not fact.origin_reference_verified
        or row.routing_node != fact.routing_node
        or any(
            a is None or b is None or not isclose(a, b, rel_tol=0, abs_tol=1e-7) for a, b in pairs
        )
    ):
        return "unknown", "reference_location_unconfirmed"
    if not fact.measurement_verified or fact.measurement_graph_revision != graph_revision:
        return "unknown", "measurement_version_unconfirmed"
    if closed_way_ids and not (
        fact.scenario_verified and set(fact.verified_closed_way_ids) == set(closed_way_ids)
    ):
        return "unknown", "scenario_conditions_unconfirmed"
    complete = (
        fact.eligible_inventory_complete
        and bool(fact.eligible_facility_ids)
        and all(
            key in targets
            and targets[key].service == "fire"
            and targets[key].coordinate_status in EXITS
            for key in fact.eligible_facility_ids
        )
    )
    if row.minutes is None:
        return (
            ("unreachable", None)
            if complete and row.state == "unreachable"
            else ("unknown", "path_unconfirmed")
        )
    if not isfinite(row.minutes) or row.minutes < 0:
        return "unknown", "path_unconfirmed"
    target = targets.get(row.facility_id or "")
    if target is None or target.id not in fact.eligible_facility_ids or target.service != "fire":
        return "unknown", "facility_profile_unconfirmed"
    if target.coordinate_status not in EXITS:
        return "unknown", "facility_entrances_unverified"
    threshold = fire_threshold(fact.settlement_type)
    if threshold is not None and row.minutes <= threshold:
        return "within", None
    return (
        ("exceeded", None)
        if complete and row.state == "exceeded"
        else ("unknown", "inventory_incomplete")
    )
