from dataclasses import replace

import pytest

from app.domain.normative.model import AccessRow
from app.domain.normative.school_rules import school_checks
from app.domain.normative.stop_rules import stop_checks
from app.domain.normative.walking_facts import WalkingFacts


def facts(service: str = "school") -> WalkingFacts:
    return WalkingFacts(
        origin_id="o",
        service=service,
        source_url="https://example.org/facts",
        observed_at="2026-11-12",
        facts_verified=True,
        legal_currentness_verified=True,
        measurement_verified=True,
        measurement_graph_revision="network",
        facility_id="f",
        eligible_inventory_complete=True,
        service_eligible=True,
        service_active=True,
        region_code="45",
        municipality_type="municipal_okrug",
        municipality_legal_id="37501000",
        settlement_legal_id="37501000001",
        settlement_category="city",
        origin_kind="residential",
        exception_800_applicable=False,
        exception_source_url="https://example.org/exception",
        sanitary_project_case="current",
        regional_planning_scope=True,
        municipal_planning_scope=True,
        bus_scope=True,
        bus_active=True,
        bus_return_trip=True,
        bus_vehicle_verified=True,
        bus_route_km=25,
        bus_approach_metres=300,
        regional_transport_km=25,
        zones=("individual_housing",),
        zone_source_url="https://example.org/zone",
        zone_version="2026",
        zoning_complete=True,
    )


def row(distance: float | None = 700) -> AccessRow:
    return AccessRow(
        "o", "Building", None, 55, 65, "f", None, None, "unknown", distance_metres=distance
    )


@pytest.mark.parametrize(
    "category,special,limit",
    [
        ("rural", True, 1000),
        ("rural", None, 1000),
        ("city", True, 800),
        ("city", False, 500),
        ("city", None, None),
        (None, False, None),
    ],
)
def test_school_radius_keeps_rural_priority_and_unknown_separate(
    category: str | None, special: bool | None, limit: float | None
) -> None:
    context = replace(facts(), settlement_category=category, exception_800_applicable=special)
    check = school_checks(row(), context)[0]
    assert check.threshold == limit
    assert check.applicability == ("unknown" if limit is None else "applicable")


def test_unknown_facts_never_select_the_catalog_500m_default() -> None:
    checks = school_checks(row(100), None)
    assert len(checks) == 6
    assert all(c.threshold is None and c.result == "unknown" for c in checks)


def test_transport_limits_have_separate_measurements_units_and_verdicts() -> None:
    checks = {c.rule_id: c for c in school_checks(row(), facts())}
    assert checks["sp4283_bus_route"].threshold == 30
    assert checks["sp4283_bus_route"].unit == "kilometres"
    assert checks["sp4283_bus_route"].result == "within"
    assert checks["rngp178_school_transport"].threshold == 15
    assert checks["rngp178_school_transport"].result == "exceeded"
    assert checks["sp4283_bus_approach"].threshold == 500
    assert checks["sp4283_bus_approach"].unit == "metres"


def test_transition_case_does_not_exempt_organized_transport() -> None:
    checks = {
        c.rule_id: c
        for c in school_checks(row(), replace(facts(), sanitary_project_case="transitional_review"))
    }
    assert checks["sp4283_school_walk"].reason == "transitional_project_review"
    assert checks["sp4283_school_walk"].result == "unknown"
    assert checks["sp4283_bus_route"].result == "within"
    assert checks["sp4283_bus_approach"].reason == "transitional_project_review"


def test_regional_transport_uses_municipality_not_settlement_type() -> None:
    context = replace(facts(), municipality_type="urban_okrug", settlement_category="rural")
    check = school_checks(row(), context)[-1]
    assert check.threshold is None
    assert check.applicability == "not_regulated"
    assert school_checks(row(), facts())[-1].threshold == 15


@pytest.mark.parametrize(
    "zone,city,expected",
    [
        ("city_centre", "37701000001", 250),
        ("industrial", "37701000001", 400),
        ("recreation", "37701000001", 800),
        ("other", "37701000001", 500),
        ("individual_housing", "37701000001", 600),
        ("individual_housing", "37501000001", 800),
    ],
)
def test_stop_limits_use_origin_zone_and_exact_settlement_id(
    zone: str, city: str, expected: float
) -> None:
    context = replace(facts("stop"), zones=(zone,), settlement_legal_id=city)
    assert stop_checks(row(), context)[0].threshold == expected


def test_unknown_zone_does_not_mean_other_and_overlaps_do_not_choose_minimum() -> None:
    assert stop_checks(row(), replace(facts("stop"), zones=()))[0].threshold is None
    assert (
        stop_checks(row(), replace(facts("stop"), zones=("other",), zoning_complete=None))[
            0
        ].threshold
        is None
    )
    conflict = stop_checks(row(100), replace(facts("stop"), zones=("city_centre", "recreation")))[0]
    assert conflict.threshold is None
    assert conflict.candidate_thresholds == (250, 800)
    assert conflict.reason == "zone_conflict"
    assert conflict.result == "unknown"


def test_rural_stop_is_not_regulated_and_other_municipality_is_not_applicable() -> None:
    checks = stop_checks(row(), replace(facts("stop"), settlement_category="rural"))
    assert checks[0].applicability == "not_regulated"
    assert checks[0].result == "not_regulated"
    assert checks[0].threshold is None
    assert checks[0].candidate_thresholds == ()
    assert checks[1].applicability == "not_applicable"


def test_municipal_and_regional_housing_rules_are_not_silently_merged() -> None:
    context = replace(facts("stop"), municipality_legal_id="37701000")
    checks = stop_checks(row(), context)
    assert [c.threshold for c in checks] == [800, 600]


def test_missing_city_id_never_infers_another_city_from_a_municipality() -> None:
    context = replace(facts("stop"), municipality_legal_id="37701000", settlement_legal_id=None)
    assert [c.threshold for c in stop_checks(row(), context)] == [None, 600]


def test_a_proxy_path_cannot_be_certified_by_a_context_flag() -> None:
    proxy = replace(row(), uncertainty=("residential_reference_not_entrance",))
    assert school_checks(proxy, facts())[0].reason == "measurement_unverified"
    assert (
        school_checks(row(), replace(facts(), legal_currentness_verified=False))[0].result
        == "unknown"
    )
    assert (
        school_checks(row(), replace(facts(), facility_id="another-school"))[0].reason
        == "target_mismatch"
    )


def test_school_catchment_and_live_bus_must_be_confirmed() -> None:
    assert school_checks(row(), replace(facts(), service_eligible=None))[0].result == "unknown"
    assert school_checks(row(), replace(facts(), bus_return_trip=None))[4].result == "unknown"


def test_verified_population_cannot_use_all_residents_as_school_children() -> None:
    with pytest.raises(ValueError, match="population group"):
        replace(
            facts(), population=10, population_group="residents", population_group_verified=True
        )
    with pytest.raises(ValueError, match="coordinates"):
        replace(facts(), entrance_verified=True)


def test_incomplete_eligible_inventory_can_confirm_a_nearby_path_but_not_a_violation() -> None:
    assert school_checks(row(700), facts())[0].result == "exceeded"
    context = replace(facts(), eligible_inventory_complete=False)
    assert school_checks(row(100), context)[0].result == "within"
    assert school_checks(row(700), context)[0].result == "unknown"
    assert school_checks(row(700), context)[0].reason == "eligible_inventory_incomplete"
