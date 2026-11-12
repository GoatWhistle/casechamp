from dataclasses import field
from typing import Literal

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass


@dataclass(config=ConfigDict(extra="forbid"))
class TrafficDevelopment:
    kind: Literal["traffic_development"]
    places: list[str] = field(default_factory=list)
    region: str = ""
    bounds: list[float] = field(default_factory=list)
    demand_multiplier: float = 1.0
    pair_flow: float = 1000.0
    max_projects: int = 3


@dataclass(config=ConfigDict(extra="forbid"))
class TrafficData:
    kind: Literal["traffic_data"]
