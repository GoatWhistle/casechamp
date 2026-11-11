from dataclasses import replace

import pytest

from app.domain.appraisal import appraise
from app.domain.appraisal_inputs import (
    DemandScenario,
    FreightFlow,
    PassengerFlow,
    ProjectAssumptions,
    TravelChange,
)
from app.domain.errors import InvalidQuery


def project() -> ProjectAssumptions:
    return ProjectAssumptions(
        [
            PassengerFlow("a", "market", 1000, 300, "Survey 2026", "observed"),
            PassengerFlow("b", "market", 200, 100, "Assumed demand"),
        ],
        [
            DemandScenario("low", 0.5, 0.8),
            DemandScenario("base", 1, 1),
            DemandScenario("high", 1.5, 1.2),
        ],
        100000,
        10000,
        2,
        0.1,
        2026,
        "Cost estimate",
        [FreightFlow("deliveries", 100, 3, 2, 100, 80, 500, 10, "Carrier estimate")],
    )


def evidence() -> list[TravelChange]:
    return [TravelChange("a", "market", 2, 1.5), TravelChange("b", "market", 1, 2)]


def test_signed_multi_od_freight_and_discounted_project_costs() -> None:
    result = appraise(project(), evidence())
    base = result.scenarios[1]
    assert result.status == "calculated"
    assert base.annual_passenger_hours == 300
    assert base.annual_passenger_rub == 130000
    assert base.annual_vehicle_hours == 100
    assert base.annual_vehicle_km == 2000
    assert base.annual_freight_rub == 70000
    assert base.annual_gross_rub == 200000
    assert base.annual_net_rub == 190000
    assert base.present_benefits_rub == pytest.approx(200000 / 1.1 + 200000 / 1.21)
    assert base.present_costs_rub == pytest.approx(100000 + 10000 / 1.1 + 10000 / 1.21)
    assert base.net_present_value_rub == pytest.approx(-100000 + 190000 / 1.1 + 190000 / 1.21)
    assert base.discounted_payback_year == 1
    assert result.scenarios[0].annual_gross_rub == 80000
    assert result.scenarios[2].annual_gross_rub == 360000


def test_missing_route_is_not_zero_benefit_or_an_infinite_windfall() -> None:
    result = appraise(project(), [TravelChange("a", "market", None, 1), evidence()[1]])
    assert result.unresolved_passenger_flows == 1
    assert result.status == "incomplete"
    assert all(
        s.annual_gross_rub is None and s.net_present_value_rub is None for s in result.scenarios
    )
    assert result.scenarios[1].annual_freight_rub == 70000


def test_losses_remain_negative_and_have_no_payback() -> None:
    result = appraise(
        replace(project(), freight=[]), [TravelChange("a", "market", 1, 2), evidence()[1]]
    )
    assert result.scenarios[1].annual_gross_rub == -320000
    assert result.scenarios[1].discounted_payback_year is None


def test_zero_discount_and_zero_cost_ratio() -> None:
    result = appraise(
        replace(project(), discount_rate=0, capital_cost_rub=0, annual_operating_cost_rub=0),
        evidence(),
    )
    assert result.scenarios[1].net_present_value_rub == 400000
    assert result.scenarios[1].benefit_cost_ratio is None


@pytest.mark.parametrize(
    "invalid",
    [
        replace(project(), discount_rate=float("nan")),
        replace(project(), horizon_years=0),
        replace(project(), capital_cost_rub=-1),
        replace(project(), cost_source=" "),
    ],
)
def test_invalid_assumptions_are_rejected(invalid: ProjectAssumptions) -> None:
    with pytest.raises(InvalidQuery):
        appraise(invalid, evidence())


def test_duplicate_flows_and_missing_evidence_are_rejected() -> None:
    with pytest.raises(InvalidQuery):
        appraise(replace(project(), passengers=[project().passengers[0]] * 2), evidence())
    with pytest.raises(InvalidQuery):
        appraise(project(), evidence()[:1])
    with pytest.raises(InvalidQuery):
        appraise(replace(project(), scenarios=list(reversed(project().scenarios))), evidence())
