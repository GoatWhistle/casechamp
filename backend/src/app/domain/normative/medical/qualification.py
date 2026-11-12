from dataclasses import replace
from datetime import datetime
from math import isclose, isfinite

from app.domain.normative.medical.facts import MedicalFacts
from app.domain.normative.model import AccessRow, AccessState, Criterion, Facility, Uncertainty
from app.domain.normative.scope import apply_population_scope

ENTRANCES = frozenset({"verified_entrance", "verified_entrance_complete_inventory"})


def apply_medical_evidence(
    criterion: Criterion,
    rows: list[AccessRow],
    facts: list[MedicalFacts],
    facilities: list[Facility],
    graph_revision: str,
    instant: datetime | None,
    closed_way_ids: list[int],
) -> list[AccessRow]:
    display = apply_population_scope(criterion, rows)
    if not facts:
        return display
    if instant is None:
        raise ValueError("Medical qualification requires a decision time")
    if any(f.service != criterion.service for f in facts):
        raise ValueError("Medical evidence belongs to another care form")
    contexts = {f.origin_id: f for f in facts}
    if len(contexts) != len(facts) or set(contexts) - {r.id for r in rows}:
        raise ValueError("Medical evidence has duplicate or unknown origins")
    active = {key: f for key, f in contexts.items() if f.facts_verified and f.active_on(instant)}
    if len({f.population_reference for f in active.values() if f.population_verified}) > 1:
        raise ValueError("Medical population references cannot be mixed")
    targets = {f.id: f for f in facilities}
    result = []
    for raw, row in zip(rows, display, strict=True):
        fact = contexts.get(row.id)
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
            population = fact.population if fact.population_verified else None
            if population is not None:
                reasons = [r for r in reasons if r != "population_group_missing"]
            if fact.catchment_verified:
                reasons = [r for r in reasons if r != "medical_catchment_unconfirmed"]
            if fact.eligible_facility_ids and all(
                key in targets and targets[key].coordinate_status in ENTRANCES
                for key in fact.eligible_facility_ids
            ):
                reasons = [r for r in reasons if r != "facility_entrances_unverified"]
            state, reason = qualified_state(
                criterion, raw, fact, targets, graph_revision, closed_way_ids
            )
            if reason:
                reasons.append(reason)
            threshold = fact.threshold_minutes if fact.regional_adjustment_verified else None
            row = replace(
                row,
                population=population,
                state=state,
                threshold_minutes=threshold,
                catchment_source_url=fact.catchment_source_url,
                threshold_source_url=fact.regional_adjustment_source_url,
                excess_minutes=max(0.0, raw.minutes - threshold)
                if state in {"within", "exceeded"}
                and raw.minutes is not None
                and threshold is not None
                else None,
            )
        result.append(replace(row, uncertainty=tuple(dict.fromkeys(reasons))))
    return result


def qualified_state(
    criterion: Criterion,
    row: AccessRow,
    fact: MedicalFacts,
    targets: dict[str, Facility],
    graph_revision: str,
    closed_way_ids: list[int],
) -> tuple[AccessState, Uncertainty | None]:
    if (
        not fact.legal_currentness_verified
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
    if not fact.ownership_scope_verified or fact.ownership_applicable is None:
        return "unknown", "ownership_scope_unconfirmed"
    if fact.ownership_applicable is False:
        return "not_applicable", None
    if not fact.regional_adjustment_verified or fact.threshold_minutes is None:
        return "unknown", "regional_adjustment_unconfirmed"
    if fact.transport_mode != "car" or not fact.transport_method_verified:
        return "unknown", "transport_mode_unconfirmed"
    if not fact.facility_form_verified:
        return "unknown", "medical_form_unconfirmed"
    if not fact.adult_profile_verified:
        return "unknown", "adult_profile_unconfirmed"
    if not fact.catchment_verified:
        return "unknown", "medical_catchment_unconfirmed"
    if fact.service_eligible is not True:
        return "unknown", "facility_profile_unconfirmed"
    if fact.service_active is not True:
        return "unknown", "service_status_unconfirmed"
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
            and targets[key].service == criterion.service
            and targets[key].coordinate_status in ENTRANCES
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
    if (
        target is None
        or target.id not in fact.eligible_facility_ids
        or target.service != fact.service
    ):
        return "unknown", "facility_profile_unconfirmed"
    if target.coordinate_status not in ENTRANCES:
        return "unknown", "facility_entrances_unverified"
    if row.minutes <= fact.threshold_minutes:
        return "within", None
    return (
        ("exceeded", None)
        if complete and row.state == "exceeded"
        else ("unknown", "inventory_incomplete")
    )
