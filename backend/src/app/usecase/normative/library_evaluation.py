from dataclasses import replace
from datetime import datetime

from app.domain.normative.library.facts import LibraryFacts
from app.domain.normative.library.qualification import ENTRANCE_STATUSES
from app.domain.normative.model import AccessRow, Facility, Origin
from app.domain.normative.territory import library_threshold
from app.usecase.normative.interface import NormativeRouting


def evaluate_library_targets(
    routing: NormativeRouting,
    origins: list[Origin],
    facilities: list[Facility],
    threshold: float,
    closed_way_ids: list[int],
    facts: list[LibraryFacts],
    instant: datetime,
) -> list[AccessRow]:
    contexts = {
        fact.origin_id: fact for fact in facts if fact.facts_verified and fact.active_on(instant)
    }
    groups: dict[tuple[tuple[str, ...] | None, bool, float], list[Origin]] = {}
    for origin in origins:
        fact = contexts.get(origin.id)
        ids: tuple[str, ...] | None = None
        complete = False
        limit = threshold
        if fact and fact.service_eligible is True:
            ids = (
                tuple(sorted(fact.eligible_facility_ids))
                if fact.service_active is not False
                else ()
            )
            complete = fact.eligible_inventory_complete
            if fact.jurisdiction_verified:
                limit = library_threshold(fact.municipality_type) or threshold
        groups.setdefault((ids, complete, limit), []).append(origin)
    result = {}
    for (ids, complete, limit), points in groups.items():
        targets = facilities if ids is None else [f for f in facilities if f.id in ids]
        if (
            ids
            and len(targets) == len(ids)
            and complete
            and all(f.coordinate_status in ENTRANCE_STATUSES for f in targets)
        ):
            targets = [
                replace(f, coordinate_status="verified_entrance_complete_inventory")
                for f in targets
            ]
        if targets:
            rows = routing.evaluate(points, targets, limit, closed_way_ids)
        else:
            rows = [
                AccessRow(
                    o.id,
                    o.name,
                    o.population,
                    o.latitude,
                    o.longitude,
                    None,
                    None,
                    None,
                    "unknown",
                    routing_node=o.node,
                    approach_metres=o.snap_km * 1000 if o.snap_km is not None else None,
                )
                for o in points
            ]
        result.update({row.id: row for row in rows})
    return [result[origin.id] for origin in origins]
