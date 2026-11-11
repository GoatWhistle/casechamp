from dataclasses import dataclass, field
from typing import Literal


@dataclass(frozen=True)
class PassengerFlow:
    origin_point_id: str
    market_city: str
    trips_per_year: float
    rub_per_hour: float
    source: str
    basis: Literal["assumed", "observed"] = "assumed"
    origin_name: str = ""


@dataclass(frozen=True)
class FreightFlow:
    name: str
    trips_per_year: float
    before_hours: float | None
    after_hours: float | None
    before_km: float | None
    after_km: float | None
    rub_per_vehicle_hour: float
    rub_per_km: float
    source: str
    basis: Literal["assumed", "observed"] = "assumed"
    origin_point_id: str = ""
    market_city: str = ""


@dataclass(frozen=True)
class FreightTravelChange:
    name: str
    before_hours: float | None
    after_hours: float | None
    before_km: float | None
    after_km: float | None


@dataclass(frozen=True)
class DemandScenario:
    name: Literal["low", "base", "high"]
    demand_factor: float
    value_factor: float


@dataclass(frozen=True)
class ProjectAssumptions:
    passengers: list[PassengerFlow]
    scenarios: list[DemandScenario]
    capital_cost_rub: float
    annual_operating_cost_rub: float
    horizon_years: int
    discount_rate: float
    price_year: int
    cost_source: str
    freight: list[FreightFlow] = field(default_factory=list)


@dataclass(frozen=True)
class TravelChange:
    origin_point_id: str
    market_city: str
    before_hours: float | None
    after_hours: float | None
