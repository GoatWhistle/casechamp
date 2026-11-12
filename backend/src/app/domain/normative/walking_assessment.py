import hashlib
import json
from dataclasses import asdict, replace

from app.domain.normative.model import AccessRow, AccessState, Origin
from app.domain.normative.rules import RuleCheck, RuleSet
from app.domain.normative.school_rules import school_checks
from app.domain.normative.stop_rules import stop_checks
from app.domain.normative.walking_facts import WalkingFacts


def apply_walking_conditions(
    service: str,
    baseline: list[AccessRow],
    scenario: list[AccessRow],
    facts: list[WalkingFacts],
    closed_way_ids: list[int] | None = None,
    graph_revision: str | None = None,
) -> tuple[list[AccessRow], list[AccessRow], tuple[RuleSet, ...]]:
    contexts = {item.origin_id: item for item in facts if item.service == service}
    if len(contexts) != sum(item.service == service for item in facts):
        raise ValueError("Conflicting walking facts")
    if service not in {"school", "stop"}:
        raise ValueError("Unsupported walking service")
    checks_for = school_checks if service == "school" else stop_checks
    groups: dict[tuple[RuleCheck, ...], RuleSet] = {}
    missing: tuple[RuleCheck, ...] | None = None

    def assess(rows: list[AccessRow], changed: bool = False) -> list[AccessRow]:
        nonlocal missing
        result = []
        for row in rows:
            context = contexts.get(row.id)
            if context is None:
                if missing is None:
                    missing = checks_for(row, None)
                checks = missing
            else:
                checks = checks_for(row, context)
                if (
                    graph_revision is not None
                    and context.measurement_graph_revision != graph_revision
                ):
                    checks = tuple(
                        replace(check, result="unknown", reason="measurement_version_mismatch")
                        if check.applicability == "applicable"
                        and check.measurement == "walking_path"
                        else check
                        for check in checks
                    )
                if changed and not (
                    context.scenario_verified
                    and set(context.verified_closed_way_ids) == set(closed_way_ids or [])
                ):
                    checks = tuple(
                        replace(check, result="unknown", reason="scenario_unverified", value=None)
                        if check.applicability == "applicable"
                        else check
                        for check in checks
                    )
            group = groups.get(checks)
            if group is None:
                content = json.dumps(
                    [asdict(check) for check in checks], sort_keys=True, ensure_ascii=False
                )
                group = RuleSet(hashlib.sha256(content.encode()).hexdigest(), checks)
                groups[checks] = group
            applicable = [check for check in checks if check.applicability == "applicable"]
            state: AccessState = "unknown"
            if any(check.result == "exceeded" for check in applicable):
                state = "exceeded"
            elif applicable and all(
                check.result in {"within", "not_applicable", "not_regulated"} for check in checks
            ):
                state = "within"
            if (
                context is not None
                and context.legal_currentness_verified
                and checks
                and all(
                    check.applicability in {"not_regulated", "not_applicable"} for check in checks
                )
            ):
                state = (
                    "not_regulated"
                    if any(check.applicability == "not_regulated" for check in checks)
                    else "not_applicable"
                )
            population = row.population
            reasons = row.uncertainty
            if context is not None and context.facts_verified:
                if context.population_group_verified:
                    population = context.population
                    reasons = tuple(
                        reason for reason in reasons if reason != "population_group_missing"
                    )
                if all(check.applicability != "unknown" for check in checks):
                    reasons = tuple(
                        reason for reason in reasons if reason != "territory_conditions_missing"
                    )
                if context.service_eligible is True and context.service_active is True:
                    reasons = tuple(
                        reason for reason in reasons if reason != "service_status_unconfirmed"
                    )
            result.append(
                replace(
                    row,
                    rule_set_id=group.id,
                    state=state,
                    population=population,
                    uncertainty=reasons,
                )
            )
        return result

    before, after = assess(baseline), assess(scenario, bool(closed_way_ids))
    return before, after, tuple(sorted(groups.values(), key=lambda group: group.id))


def walking_entrances(origins: list[Origin], facts: list[WalkingFacts]) -> list[Origin]:
    verified = {
        item.origin_id: item for item in facts if item.facts_verified and item.entrance_verified
    }
    if not verified:
        return origins
    result = []
    for origin in origins:
        context = verified.get(origin.id)
        if context is not None:
            if context.origin_kind != "residential":
                raise ValueError("Residential origin sets cannot contain other population cohorts")
            origin = replace(
                origin,
                latitude=context.entrance_latitude,
                longitude=context.entrance_longitude,
                node=None,
                snap_km=None,
                entrance_verified=True,
            )
        result.append(origin)
    return result
