from app.domain.normative.model import AccessRow, Facility, Origin
from app.domain.normative.walking_facts import WalkingFacts
from app.usecase.normative.interface import NormativeRouting


def evaluate_walking_targets(
    routing: NormativeRouting,
    origins: list[Origin],
    facilities: list[Facility],
    threshold: float,
    closed_way_ids: list[int],
    facts: list[WalkingFacts],
) -> list[AccessRow]:
    contexts = {fact.origin_id: fact for fact in facts}
    groups: dict[tuple[str, ...] | None, list[Origin]] = {}
    for origin in origins:
        context = contexts.get(origin.id)
        allowed: tuple[str, ...] | None = None
        if context is not None and context.facts_verified and context.service_eligible is True:
            ids = context.eligible_facility_ids or (
                (context.facility_id,) if context.facility_id else ()
            )
            if ids or context.eligible_inventory_complete:
                allowed = tuple(sorted(set(ids)))
        groups.setdefault(allowed, []).append(origin)
    result: dict[str, AccessRow] = {}
    for allowed, points in groups.items():
        targets = facilities if allowed is None else [f for f in facilities if f.id in allowed]
        if targets:
            evaluated = routing.evaluate(points, targets, threshold, closed_way_ids)
        else:
            evaluated = [
                AccessRow(
                    origin.id,
                    origin.name,
                    None,
                    origin.latitude,
                    origin.longitude,
                    None,
                    None,
                    None,
                    "unknown",
                    uncertainty=("facility_profile_unconfirmed", "population_group_missing"),
                )
                for origin in points
            ]
        result.update({row.id: row for row in evaluated})
    return [result[origin.id] for origin in origins]
