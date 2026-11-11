from dataclasses import dataclass, field
from math import isfinite

from app.domain.appraisal_inputs import FreightTravelChange, ProjectAssumptions, TravelChange
from app.domain.appraisal_validation import validate_project
from app.domain.errors import InvalidQuery


@dataclass(frozen=True)
class AppraisalScenario:
    name: str
    annual_passenger_hours: float | None
    annual_passenger_rub: float | None
    annual_vehicle_hours: float | None
    annual_vehicle_km: float | None
    annual_freight_rub: float | None
    annual_gross_rub: float | None
    annual_net_rub: float | None
    present_benefits_rub: float | None
    present_costs_rub: float
    net_present_value_rub: float | None
    benefit_cost_ratio: float | None
    discounted_payback_year: int | None


@dataclass(frozen=True)
class AppraisalReport:
    status: str
    travel: list[TravelChange]
    unresolved_passenger_flows: int
    evaluated_passenger_flows: int
    scenarios: list[AppraisalScenario]
    method: str = "conditional_flow_appraisal_v1"
    scope: str = "supplied_flows_only"
    freight_travel: list[FreightTravelChange] = field(default_factory=list)
    unresolved_freight_flows: int = 0
    freight_routing_scope: str = "manual_supplied_travel"


def appraise(
    project: ProjectAssumptions,
    travel: list[TravelChange],
    freight_travel: list[FreightTravelChange] | None = None,
) -> AppraisalReport:
    validate_project(project)
    lookup = {(r.origin_point_id, r.market_city): r for r in travel}
    if len(lookup) != len(travel) or set(lookup) != {
        (p.origin_point_id, p.market_city) for p in project.passengers
    }:
        raise InvalidQuery("Travel evidence must match the supplied passenger OD pairs")
    hours = passenger_rub = 0.0
    unresolved = 0
    for flow in project.passengers:
        change = lookup[(flow.origin_point_id, flow.market_city)]
        before, after = change.before_hours, change.after_hours
        if before is None or after is None:
            unresolved += 1
            continue
        if not all(isfinite(v) and v >= 0 for v in (before, after)):
            raise InvalidQuery("Travel evidence must be nonnegative and finite or unavailable")
        saved = (before - after) * flow.trips_per_year
        hours += saved
        passenger_rub += saved * flow.rub_per_hour
    freight_lookup = {row.name: row for row in freight_travel or []}
    routed_names = {f.name for f in project.freight if f.origin_point_id}
    if len(freight_lookup) != len(freight_travel or []) or set(freight_lookup) != routed_names:
        raise InvalidQuery("Freight travel evidence must match the supplied routed flows")
    vehicle_hours = vehicle_km = freight_rub = 0.0
    unresolved_freight = 0
    for freight_flow in project.freight:
        row = freight_lookup[freight_flow.name] if freight_flow.origin_point_id else freight_flow
        before_h, after_h, before_km, after_km = (
            row.before_hours,
            row.after_hours,
            row.before_km,
            row.after_km,
        )
        if before_h is None or after_h is None or before_km is None or after_km is None:
            unresolved_freight += 1
            continue
        if not all(isfinite(v) and v >= 0 for v in (before_h, after_h, before_km, after_km)):
            raise InvalidQuery("Freight route evidence must be finite and nonnegative")
        saved_h = (before_h - after_h) * freight_flow.trips_per_year
        saved_km = (before_km - after_km) * freight_flow.trips_per_year
        vehicle_hours += saved_h
        vehicle_km += saved_km
        freight_rub += (
            saved_h * freight_flow.rub_per_vehicle_hour + saved_km * freight_flow.rub_per_km
        )
    factors = [(1 + project.discount_rate) ** -year for year in range(1, project.horizon_years + 1)]
    present_costs = project.capital_cost_rub + project.annual_operating_cost_rub * sum(factors)
    results = []
    for scenario in project.scenarios:
        demand = scenario.demand_factor
        value = scenario.value_factor
        passenger = passenger_rub * demand * value if not unresolved else None
        freight = freight_rub * demand * value if not unresolved_freight else None
        gross = passenger + freight if passenger is not None and freight is not None else None
        net = gross - project.annual_operating_cost_rub if gross is not None else None
        benefits = gross * sum(factors) if gross is not None else None
        cumulative = -project.capital_cost_rub
        payback = None
        if net is not None and net > 0 and project.capital_cost_rub > 0:
            for year, factor in enumerate(factors, 1):
                cumulative += net * factor
                if cumulative >= 0:
                    payback = year
                    break
        results.append(
            AppraisalScenario(
                scenario.name,
                hours * demand if not unresolved else None,
                passenger,
                vehicle_hours * demand if not unresolved_freight else None,
                vehicle_km * demand if not unresolved_freight else None,
                freight,
                gross,
                net,
                benefits,
                present_costs,
                benefits - present_costs if benefits is not None else None,
                benefits / present_costs if benefits is not None and present_costs > 0 else None,
                payback,
            )
        )
    return AppraisalReport(
        "incomplete" if unresolved or unresolved_freight else "calculated",
        travel,
        unresolved,
        len(project.passengers) - unresolved,
        results,
        method="conditional_flow_appraisal_v2" if routed_names else "conditional_flow_appraisal_v1",
        freight_travel=freight_travel or [],
        unresolved_freight_flows=unresolved_freight,
        freight_routing_scope="road_network_vehicle_constraints_unverified"
        if routed_names
        else "manual_supplied_travel",
    )
