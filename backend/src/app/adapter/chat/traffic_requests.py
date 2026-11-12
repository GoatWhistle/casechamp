from dataclasses import field
from typing import Literal

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from app.usecase.traffic import TrafficHypothesis


@dataclass(config=ConfigDict(extra="forbid"))
class TrafficDevelopment:
    kind: Literal["traffic_development"]
    places: list[str] = field(default_factory=list)
    region: str = ""
    regions: list[str] = field(default_factory=list)
    bounds: list[float] = field(default_factory=list)
    demand_multiplier: float = 1.0
    pair_flow: float = 1000.0
    max_projects: int = 3
    objective: Literal["connectivity", "transit", "congestion"] = "connectivity"
    focus_bounds: list[float] = field(default_factory=list)
    hypotheses: list[TrafficHypothesis] = field(default_factory=list)


@dataclass(config=ConfigDict(extra="forbid"))
class TrafficData:
    kind: Literal["traffic_data"]
