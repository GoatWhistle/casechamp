from typing import Literal

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass


@dataclass(config=ConfigDict(extra="forbid"))
class RoadSearch:
    kind: Literal["road"]
    origin: str
    destination: str
    road_name: str | None = None


@dataclass(config=ConfigDict(extra="forbid"))
class BridgeSearch:
    kind: Literal["bridges"]
    near: str
    radius_km: float = 20
    name: str = ""


@dataclass(config=ConfigDict(extra="forbid"))
class ServiceSearch:
    kind: Literal["services"]
    network: Literal["intercity", "local"]
    place: str
    scenario: Literal["road", "summer", "winter"] = "road"
    mode: (
        Literal["rail", "air", "river", "ferry", "winter_road", "ice_crossing", "pontoon_bridge"]
        | None
    ) = None


@dataclass(config=ConfigDict(extra="forbid"))
class GraphPlaceSearch:
    kind: Literal["graph_places"]
    query: str
    region_id: str | None = None


@dataclass(config=ConfigDict(extra="forbid"))
class RoadViewportSearch:
    kind: Literal["road_viewport"]
    west: float
    south: float
    east: float
    north: float
    zoom: float = 10


type TransportSearch = (
    RoadSearch | BridgeSearch | ServiceSearch | GraphPlaceSearch | RoadViewportSearch
)
