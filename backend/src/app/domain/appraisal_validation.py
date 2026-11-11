from math import isfinite

from app.domain.appraisal_inputs import FreightFlow, PassengerFlow, ProjectAssumptions
from app.domain.errors import InvalidQuery


def bounded(value: float, maximum: float) -> bool:
    return isfinite(value) and 0 <= value <= maximum


def validate_project(project: ProjectAssumptions) -> None:
    if not 1 <= len(project.passengers) + len(project.freight) <= 1000:
        raise InvalidQuery("Supply between 1 and 1000 documented flows")
    if len({(p.origin_point_id, p.market_city) for p in project.passengers}) != len(
        project.passengers
    ):
        raise InvalidQuery("Duplicate passenger OD pairs")
    if len({f.name.strip() for f in project.freight}) != len(project.freight):
        raise InvalidQuery("Duplicate freight flow names")
    if [s.name for s in project.scenarios] != ["low", "base", "high"]:
        raise InvalidQuery("Supply low, base and high scenarios in order")
    for attribute in ("demand_factor", "value_factor"):
        values = [getattr(s, attribute) for s in project.scenarios]
        if not all(bounded(v, 100) for v in values) or values != sorted(values):
            raise InvalidQuery("Scenario factors must be ordered, finite and between 0 and 100")
    if not (
        isinstance(project.horizon_years, int)
        and 1 <= project.horizon_years <= 100
        and isinstance(project.price_year, int)
        and 2000 <= project.price_year <= 2100
        and bounded(project.discount_rate, 1)
        and bounded(project.capital_cost_rub, 1e15)
        and bounded(project.annual_operating_cost_rub, 1e15)
        and 1 <= len(project.cost_source.strip()) <= 1000
    ):
        raise InvalidQuery("Invalid project costs, horizon, price year, source or discount rate")
    flows: list[PassengerFlow | FreightFlow] = [*project.passengers, *project.freight]
    for flow in flows:
        if not (
            bounded(flow.trips_per_year, 1e10)
            and 1 <= len(flow.source.strip()) <= 1000
            and flow.basis in {"assumed", "observed"}
        ):
            raise InvalidQuery("Every flow requires finite demand and a source or assumption")
    for passenger in project.passengers:
        if not (
            1 <= len(passenger.origin_point_id.strip()) <= 200
            and 1 <= len(passenger.market_city.strip()) <= 200
            and bounded(passenger.rub_per_hour, 1e8)
        ):
            raise InvalidQuery("Invalid passenger OD pair or value of time")
    for freight in project.freight:
        routed = bool(freight.origin_point_id or freight.market_city)
        if routed and not (
            1 <= len(freight.origin_point_id.strip()) <= 200
            and 1 <= len(freight.market_city.strip()) <= 200
        ):
            raise InvalidQuery("Routed freight requires both origin point and market city")
        if not 1 <= len(freight.name.strip()) <= 200 or not all(
            bounded(v, 1e8) for v in (freight.rub_per_vehicle_hour, freight.rub_per_km)
        ):
            raise InvalidQuery("Invalid freight rates")
        if any(
            v is not None and not bounded(v, 1e8)
            for v in (
                freight.before_hours,
                freight.after_hours,
                freight.before_km,
                freight.after_km,
            )
        ):
            raise InvalidQuery("Supplied freight travel must be finite and nonnegative")
        if not routed and not all(
            v is not None and bounded(v, 1e8)
            for v in (
                freight.before_hours,
                freight.after_hours,
                freight.before_km,
                freight.after_km,
            )
        ):
            raise InvalidQuery("Manual freight requires finite time and mileage assumptions")
