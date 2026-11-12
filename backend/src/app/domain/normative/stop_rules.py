from app.domain.normative.model import AccessRow
from app.domain.normative.rules import (
    Choice,
    RuleCheck,
    RuleId,
    assessed_rule,
    available,
    planning_scope,
)
from app.domain.normative.walking_facts import WalkingFacts

STOP_RULES: tuple[RuleId, ...] = ("rngp178_stop_walk", "mngp114_stop_walk")
ZONES = {"city_centre": 250, "industrial": 400, "recreation": 800, "other": 500}


def stop_checks(row: AccessRow, facts: WalkingFacts | None) -> tuple[RuleCheck, ...]:
    missing = available(facts)
    if missing is not None or facts is None:
        return tuple(assessed_rule(key, missing or Choice(), row, facts) for key in STOP_RULES)
    return tuple(
        assessed_rule(key, stop_choice(facts, index == 1), row, facts)
        for index, key in enumerate(STOP_RULES)
    )


def stop_choice(facts: WalkingFacts, municipal: bool) -> Choice:
    outside = planning_scope(facts, municipal)
    if outside is not None:
        return outside
    if facts.origin_kind is None:
        return Choice(reason="origin_profile_unknown")
    if facts.settlement_category is None:
        return Choice(reason="settlement_unknown")
    if facts.settlement_category == "rural":
        return (
            Choice(reason="municipal_rural_scope_review", candidates=())
            if municipal
            else Choice("not_regulated", reason="rural_not_regulated")
        )
    if not facts.zones or not facts.zone_source_url or not facts.zone_version:
        return Choice(reason="zone_unknown")
    if len(facts.zones) > 1:
        candidates: set[float] = set()
        for zone in facts.zones:
            candidates.update(zone_limit(facts, zone, municipal).candidates or ())
            threshold = zone_limit(facts, zone, municipal).threshold
            if threshold is not None:
                candidates.add(threshold)
        return Choice(reason="zone_conflict", candidates=tuple(sorted(candidates)))
    return zone_limit(facts, facts.zones[0], municipal)


def zone_limit(facts: WalkingFacts, zone: str, municipal: bool) -> Choice:
    if zone == "other" and facts.zoning_complete is not True:
        return Choice(reason="zoning_incomplete")
    if zone != "individual_housing":
        return Choice("applicable", ZONES[zone], "zone_selected")
    if municipal:
        return Choice("applicable", 600, "kurgan_municipality_housing")
    if facts.settlement_legal_id is None:
        return Choice(reason="settlement_id_unknown", candidates=(600, 800))
    if facts.settlement_category != "city":
        return Choice(reason="city_category_review", candidates=())
    return Choice(
        "applicable", 600 if facts.settlement_legal_id == "37701000001" else 800, "city_housing"
    )
