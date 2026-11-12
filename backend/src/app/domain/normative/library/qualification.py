from dataclasses import replace
from datetime import datetime
from math import isclose, isfinite

from app.domain.normative.library.facts import LibraryFacts
from app.domain.normative.model import AccessRow, AccessState, Criterion, Facility, Uncertainty
from app.domain.normative.territory import (
    TerritoryContext,
    apply_library_conditions,
    library_threshold,
)

ENTRANCE_STATUSES = frozenset({"verified_entrance", "verified_entrance_complete_inventory"})


def apply_library_evidence(
    criterion: Criterion,
    rows: list[AccessRow],
    territories: list[TerritoryContext],
    facts: list[LibraryFacts],
    facilities: list[Facility],
    graph_revision: str,
    instant: datetime,
    closed_way_ids: list[int],
) -> list[AccessRow]:
    display = apply_library_conditions(rows, territories)
    if not facts:
        return display
    contexts = {fact.origin_id: fact for fact in facts}
    if len(contexts) != len(facts) or set(contexts) - {row.id for row in rows}:
        raise ValueError("Library evidence has duplicate or unknown origins")
    active = {
        key: fact
        for key, fact in contexts.items()
        if fact.facts_verified and fact.active_on(instant)
    }
    references = {f.population_reference for f in active.values() if f.population_verified}
    if len(references) > 1:
        raise ValueError("Library population references cannot be mixed")
    targets = {facility.id: facility for facility in facilities}
    jurisdictions = {context.point_id: context for context in territories}
    result = []
    for raw, row in zip(rows, display, strict=True):
        fact = contexts.get(row.id)
        if active:
            verified_population = active.get(row.id)
            population = (
                verified_population.population
                if verified_population and verified_population.population_verified
                else None
            )
            row = replace(row, population=population)
            if population is None:
                row = replace(
                    row,
                    uncertainty=tuple(
                        dict.fromkeys((*row.uncertainty, "population_group_missing"))
                    ),
                )
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
            previous = jurisdictions.get(row.id)
            if fact.jurisdiction_verified:
                if (
                    previous
                    and previous.verification_status == "primary_verified"
                    and (
                        previous.municipality_type != fact.municipality_type
                        or previous.municipality_code is not None
                        and previous.municipality_code != fact.municipality_code
                    )
                ):
                    raise ValueError("Conflicting verified municipality evidence")
                row = replace(
                    row,
                    threshold_minutes=library_threshold(fact.municipality_type),
                    territory_type=fact.municipality_type,
                    municipality_code=fact.municipality_code,
                    territory_source_url=fact.source_url,
                    territory_verification_status="verified_library_jurisdiction",
                    territory_structure_source_url=None,
                )
                reasons = [r for r in reasons if r != "territory_conditions_missing"]
            if fact.transport_mode == "car" and fact.transport_method_verified:
                reasons = [r for r in reasons if r != "transport_mode_unconfirmed"]
            if fact.service_eligible is True:
                reasons = [r for r in reasons if r != "facility_profile_unconfirmed"]
            if fact.service_active is not True:
                reasons.append("service_status_unconfirmed")
            known = [targets[key] for key in fact.eligible_facility_ids if key in targets]
            entrances = len(known) == len(fact.eligible_facility_ids) and all(
                f.coordinate_status in ENTRANCE_STATUSES for f in known
            )
            if entrances and known:
                reasons = [r for r in reasons if r != "facility_entrances_unverified"]
            state, reason = qualified_state(
                criterion, raw, fact, targets, graph_revision, closed_way_ids
            )
            if reason:
                reasons.append(reason)
            row = replace(
                row,
                state=state,
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
    fact: LibraryFacts,
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
    if fact.transport_mode != "car" or not fact.transport_method_verified:
        return "unknown", "transport_mode_unconfirmed"
    values = [
        (row.latitude, fact.origin_latitude),
        (row.longitude, fact.origin_longitude),
        (row.approach_metres, fact.approach_metres),
    ]
    if (
        not fact.origin_reference_verified
        or row.routing_node != fact.routing_node
        or any(
            a is None or b is None or not isclose(a, b, rel_tol=0, abs_tol=1e-7) for a, b in values
        )
    ):
        return "unknown", "reference_location_unconfirmed"
    if not fact.measurement_verified or fact.measurement_graph_revision != graph_revision:
        return "unknown", "measurement_version_unconfirmed"
    if closed_way_ids and not (
        fact.scenario_verified and set(fact.verified_closed_way_ids) == set(closed_way_ids)
    ):
        return "unknown", "scenario_conditions_unconfirmed"
    if fact.service_eligible is not True:
        return "unknown", "facility_profile_unconfirmed"
    if fact.service_active is not True:
        return "unknown", "service_status_unconfirmed"
    complete = (
        fact.eligible_inventory_complete
        and bool(fact.eligible_facility_ids)
        and all(
            key in targets
            and targets[key].service == "library"
            and targets[key].coordinate_status in ENTRANCE_STATUSES
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
    if target is None or target.id not in fact.eligible_facility_ids or target.service != "library":
        return "unknown", "facility_profile_unconfirmed"
    if target.coordinate_status not in ENTRANCE_STATUSES:
        return "unknown", "facility_entrances_unverified"
    threshold = library_threshold(fact.municipality_type)
    if threshold is None:
        return "unknown", "territory_conditions_missing"
    if row.minutes <= threshold:
        return "within", None
    return (
        ("exceeded", None)
        if complete and row.state == "exceeded"
        else ("unknown", "inventory_incomplete")
    )
