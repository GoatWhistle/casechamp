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

SCHOOL_RULES: tuple[RuleId, ...] = (
    "sp4283_school_walk",
    "rngp178_school_walk",
    "mngp114_school_walk",
    "sp4283_bus_approach",
    "sp4283_bus_route",
    "rngp178_school_transport",
)


def school_checks(row: AccessRow, facts: WalkingFacts | None) -> tuple[RuleCheck, ...]:
    missing = available(facts)
    if missing is not None or facts is None:
        return tuple(assessed_rule(key, missing or Choice(), row, facts) for key in SCHOOL_RULES)
    choices = (
        sanitary_walk(facts),
        planning_walk(facts, False),
        planning_walk(facts, True),
        bus_approach(facts),
        bus_route(facts),
        planning_transport(facts),
    )
    return tuple(
        assessed_rule(key, choice, row, facts)
        for key, choice in zip(SCHOOL_RULES, choices, strict=True)
    )


def radius(facts: WalkingFacts, rural: bool) -> Choice:
    if facts.origin_kind != "residential":
        return Choice(reason="origin_profile_unknown")
    if rural:
        if facts.settlement_category is None:
            return Choice(reason="settlement_unknown")
        if facts.settlement_category == "rural":
            return Choice("applicable", 1000, "rural_branch")
    if facts.exception_800_applicable is None or not facts.exception_source_url:
        return Choice(reason="exception_unknown", candidates=(500, 800))
    return Choice("applicable", 800 if facts.exception_800_applicable else 500, "exception_checked")


def sanitary_walk(facts: WalkingFacts) -> Choice:
    if facts.sanitary_project_case is None:
        return Choice(reason="project_scope_unknown")
    if facts.sanitary_project_case == "transitional_review":
        return Choice(reason="transitional_project_review", candidates=())
    if facts.origin_kind == "child_residential_institution":
        return Choice("applicable", 1000, "institution_branch")
    return radius(facts, True)


def planning_walk(facts: WalkingFacts, municipal: bool) -> Choice:
    outside = planning_scope(facts, municipal)
    if outside is not None:
        return outside
    return radius(facts, not municipal)


def bus_scope(facts: WalkingFacts) -> Choice | None:
    if facts.bus_scope is None:
        return Choice(reason="bus_scope_unknown")
    if not facts.bus_scope:
        return Choice("not_applicable", reason="outside_bus_scope")
    return None


def bus_approach(facts: WalkingFacts) -> Choice:
    outside = bus_scope(facts)
    if outside is not None:
        return outside
    if facts.sanitary_project_case is None:
        return Choice(reason="project_scope_unknown")
    if facts.sanitary_project_case == "transitional_review":
        return Choice(reason="transitional_project_review", candidates=())
    if facts.origin_kind != "residential":
        return Choice(reason="origin_profile_unknown")
    if facts.settlement_category is None:
        return Choice(reason="settlement_unknown")
    return Choice(
        "applicable", 1000 if facts.settlement_category == "rural" else 500, "bus_collection_point"
    )


def bus_route(facts: WalkingFacts) -> Choice:
    return bus_scope(facts) or Choice("applicable", 30, "organized_transport_limit")


def planning_transport(facts: WalkingFacts) -> Choice:
    outside = planning_scope(facts, False)
    if outside is not None:
        return outside
    if facts.origin_kind != "residential":
        return Choice(reason="origin_profile_unknown")
    if facts.municipality_type is None:
        return Choice(reason="municipality_type_unknown")
    if facts.municipality_type == "urban_okrug":
        return Choice("not_regulated", reason="no_numerical_limit")
    return Choice("applicable", 15, "municipal_okrug_transport")
