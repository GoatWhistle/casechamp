from dataclasses import dataclass, field
from math import isfinite
from typing import Protocol

from app.domain.errors import DataUnavailable, InvalidQuery
from app.domain.traffic_diversion import TrafficAssumptions
from app.usecase.connectivity import ConnectivityMode, ConnectivityResult, validate_selection
from app.usecase.road_graph import RoadChange, RoadJob


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
    changes: list[RoadChange] = field(default_factory=list)


@dataclass(frozen=True)
class RoadRoute:
    corridor: RoadCorridor
    travel_hours: float
    routing_method: str = "bidirectional_dijkstra"


@dataclass(frozen=True)
class BridgeCandidate:
    corridor: RoadCorridor
    distance_km: float
    references: list[str]


class CorridorPort(Protocol):
    def read_connectivity(self, calculation_id: str) -> str: ...
    def recent_connectivity(self) -> str: ...
    def connectivity(
        self, places: list[str], mode: ConnectivityMode, center: str | None,
        closed_way_ids: list[int], traffic: TrafficAssumptions | None = None,
    ) -> ConnectivityResult: ...
    def get(self, corridor_id: str) -> RoadCorridor: ...
    def resolve(self, road_name: str, origin: str, destination: str) -> RoadCorridor: ...
    def resolve_route(self, origin: str, destination: str) -> RoadRoute: ...
    def close(self, corridor_ids: list[str]) -> list[RoadJob]: ...
    def edit(self, corridor_ids: list[str], speed_factor: float) -> list[RoadJob]: ...
    def bridges(self, near: str, radius_km: float, name: str) -> list[BridgeCandidate]: ...
    def combine_bridges(self, bridge_ids: list[str]) -> RoadCorridor: ...


class RoadCorridors:
    def __init__(self, engine: CorridorPort | None) -> None:
        self.engine = engine

    def read_connectivity(self, calculation_id: str) -> str:
        if self.engine is None:
            raise DataUnavailable("GRAPH_DIR is not configured")
        return self.engine.read_connectivity(calculation_id)

    def recent_connectivity(self) -> str:
        if self.engine is None:
            return "[]"
        return self.engine.recent_connectivity()

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

    def connectivity(
        self, places: list[str], mode: ConnectivityMode = "all_pairs",
        center: str | None = None, selection_ids: list[str] | None = None,
        traffic: TrafficAssumptions | None = None,
    ) -> ConnectivityResult:
        if self.engine is None:
            raise DataUnavailable("GRAPH_DIR is not configured")
        validate_selection(places, mode, center)
        if traffic is not None:
            traffic.validate()
            if len(places) > 4:
                raise InvalidQuery("Traffic diversion supports up to four settlements per comparison")
        selected = selection_ids or []
        if len(selected) > 20 or len(set(selected)) != len(selected):
            raise InvalidQuery("Select up to 20 distinct resolved closure IDs")
        ways = sorted({way for key in selected for way in self.get(key).way_ids})
        if selected and not ways:
            raise InvalidQuery("Selected closure contains no road ways")
        return self.engine.connectivity(places, mode, center, ways, traffic)

    def resolve_route(self, origin: str, destination: str) -> RoadRoute:
        if self.engine is None:
            raise DataUnavailable("GRAPH_DIR is not configured")
        if any(not 2 <= len(s.strip()) <= 100 for s in (origin, destination)):
            raise InvalidQuery("Specify two settlements")
        return self.engine.resolve_route(origin.strip(), destination.strip())

    def close(self, corridor_ids: list[str]) -> list[RoadJob]:
        if self.engine is None:
            raise DataUnavailable("GRAPH_DIR is not configured")
        if not 1 <= len(corridor_ids) <= 10 or len(set(corridor_ids)) != len(corridor_ids):
            raise InvalidQuery("Select between 1 and 10 distinct resolved corridor IDs")
        return self.engine.close(corridor_ids)

    def edit(self, corridor_ids: list[str], speed_factor: float) -> list[RoadJob]:
        if self.engine is None:
            raise DataUnavailable("GRAPH_DIR is not configured")
        if not 1 <= len(corridor_ids) <= 10 or len(set(corridor_ids)) != len(corridor_ids):
            raise InvalidQuery("Select between 1 and 10 distinct resolved corridor IDs")
        if not isfinite(speed_factor) or not 0 < speed_factor <= 3:
            raise InvalidQuery("Speed factor must be finite and in (0, 3]; use closure for zero")
        return self.engine.edit(corridor_ids, speed_factor)

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
