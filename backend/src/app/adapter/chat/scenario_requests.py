from dataclasses import field
from typing import Literal

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from app.adapter.chat.traffic_requests import TrafficData
from app.domain.appraisal_inputs import ProjectAssumptions
from app.usecase.connectivity import ConnectivityMode


@dataclass(config=ConfigDict(extra="forbid"))
class ServiceEdit:
    action: Literal["add", "remove"]
    network: Literal["intercity", "local"]
    mode: Literal["rail", "air", "river", "ferry", "winter_road", "ice_crossing", "pontoon_bridge"]
    source: str
    target: str
    hours: float | None = None


@dataclass(config=ConfigDict(extra="forbid"))
class NetworkScenario:
    kind: Literal["network"]
    region_ids: list[str]
    scenario: Literal["road", "summer", "winter"]
    links: list[ServiceEdit] = field(default_factory=list)
    appraisal: ProjectAssumptions | None = None


@dataclass(config=ConfigDict(extra="forbid"))
class SelectionClosure:
    kind: Literal["close_selection"]
    selection_ids: list[str]
    assessment: Literal["impact", "hansen"] = "impact"
    parent_id: str | None = None
    region_ids: list[str] = field(default_factory=list)


@dataclass(config=ConfigDict(extra="forbid"))
class AnalysisScenario:
    kind: Literal["road_analysis"]
    region_id: str
    mode: Literal["criticality"]
    percent: int = 20


@dataclass(config=ConfigDict(extra="forbid"))
class ConnectivityScenario:
    kind: Literal["connectivity"]
    places: list[str]
    mode: ConnectivityMode = "all_pairs"
    center: str | None = None
    selection_ids: list[str] = field(default_factory=list)


type TransportScenario = (
    NetworkScenario
    | SelectionClosure
    | AnalysisScenario
    | ConnectivityScenario
)


@dataclass(config=ConfigDict(extra="forbid"))
class CalculationQuery:
    kind: Literal["status", "cancel"]
    calculation_id: str
    calculation_type: Literal["scenario", "analysis", "connectivity", "traffic"] = "scenario"
    detail: Literal["summary", "full"] = "summary"


@dataclass(config=ConfigDict(extra="forbid"))
class RecentCalculations:
    kind: Literal["recent"]


@dataclass(config=ConfigDict(extra="forbid"))
class ContinueAnalysis:
    kind: Literal["continue_analysis"]
    calculation_id: str


@dataclass(config=ConfigDict(extra="forbid"))
class ConnectivityEconomics:
    kind: Literal["connectivity_economics"]
    calculation_id: str
    value_of_pcu_hour_rub: float = 500


@dataclass(config=ConfigDict(extra="forbid"))
class ComparisonTable:
    kind: Literal["table"]
    scenario_ids: list[str] = field(default_factory=list)
    stress_ids: list[str] = field(default_factory=list)
    view: Literal["indices", "routes", "access"] = "indices"
    regions: list[str] = field(default_factory=list)


type CalculationRequest = (
    TrafficData
    | CalculationQuery
    | RecentCalculations
    | ContinueAnalysis
    | ConnectivityEconomics
    | ComparisonTable
)
