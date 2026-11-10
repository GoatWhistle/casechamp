from dataclasses import dataclass
from math import isfinite
from typing import Protocol

from app.domain.errors import DataUnavailable, InvalidQuery
from app.usecase.road_graph import RoadJob


@dataclass(frozen=True)
class CorridorRegion:
    id: str
    name: str


@dataclass(frozen=True)
class RoadCorridor:
    id: str
    road_ref: str
    origin: str
    destination: str
    way_ids: list[int]
    length_km: float
    origin_attachment_km: float
    destination_attachment_km: float
    regions: list[CorridorRegion]
    lines: list[list[list[float]]]
    scope: str = "whole_osm_ways_on_named_road_corridor_both_directions"


@dataclass(frozen=True)
class CorridorCalculation:
    corridor: RoadCorridor
    job_ids: list[str]


@dataclass(frozen=True)
class BridgeCandidate:
    corridor: RoadCorridor
    distance_km: float
    references: list[str]


class CorridorPort(Protocol):
    def get(self, corridor_id: str) -> RoadCorridor: ...
    def resolve(self, road_name: str, origin: str, destination: str) -> RoadCorridor: ...
    def close(self, corridor_ids: list[str]) -> list[RoadJob]: ...
    def bridges(self, near: str, radius_km: float, name: str) -> list[BridgeCandidate]: ...
    def combine_bridges(self, bridge_ids: list[str]) -> RoadCorridor: ...


class RoadCorridors:
    def __init__(self, engine: CorridorPort | None) -> None:
        self.engine = engine

    def resolve(self, road_name: str, origin: str, destination: str) -> RoadCorridor:
        if self.engine is None:
            raise DataUnavailable("GRAPH_DIR is not configured")
        if any(not 2 <= len(s.strip()) <= 100 for s in (road_name, origin, destination)):
            raise InvalidQuery("Specify road name and two settlements")
        return self.engine.resolve(road_name.strip(), origin.strip(), destination.strip())

    def get(self, corridor_id: str) -> RoadCorridor:
        if self.engine is None:
            raise DataUnavailable("GRAPH_DIR is not configured")
        return self.engine.get(corridor_id)

    def close(self, corridor_ids: list[str]) -> list[RoadJob]:
        if self.engine is None:
            raise DataUnavailable("GRAPH_DIR is not configured")
        if not 1 <= len(corridor_ids) <= 10 or len(set(corridor_ids)) != len(corridor_ids):
            raise InvalidQuery("Select between 1 and 10 distinct resolved corridor IDs")
        return self.engine.close(corridor_ids)

    def combined(self, corridor_ids: list[str]) -> RoadCorridor:
        corridors = [self.get(key) for key in corridor_ids]
        if len(corridors) == 1:
            return corridors[0]
        regions = {r.id: r for c in corridors for r in c.regions}
        return RoadCorridor(
            "+".join(c.id for c in corridors),
            "; ".join(dict.fromkeys(c.road_ref for c in corridors)),
            corridors[0].origin,
            corridors[-1].destination,
            sorted({w for c in corridors for w in c.way_ids}),
            sum(c.length_km for c in corridors),
            max(c.origin_attachment_km for c in corridors),
            max(c.destination_attachment_km for c in corridors),
            list(regions.values()),
            [line for c in corridors for line in c.lines],
            "combined_named_road_corridors_both_directions",
        )

    def bridges(self, near: str, radius_km: float = 20, name: str = "") -> list[BridgeCandidate]:
        if self.engine is None:
            raise DataUnavailable("GRAPH_DIR is not configured")
        if not 2 <= len(near.strip()) <= 100 or len(name) > 100:
            raise InvalidQuery("Specify a settlement and optional bridge name or road reference")
        if not isfinite(radius_km) or not 0 < radius_km <= 50:
            raise InvalidQuery("Bridge search radius must be between 0 and 50 km")
        return self.engine.bridges(near.strip(), radius_km, name.strip())

    def combine_bridges(self, bridge_ids: list[str]) -> RoadCorridor:
        if self.engine is None:
            raise DataUnavailable("GRAPH_DIR is not configured")
        if not 1 <= len(bridge_ids) <= 20 or len(set(bridge_ids)) != len(bridge_ids):
            raise InvalidQuery("Select between 1 and 20 distinct bridge candidate IDs")
        return self.engine.combine_bridges(bridge_ids)
