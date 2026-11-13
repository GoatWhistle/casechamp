from dataclasses import dataclass, field
from typing import Literal, Protocol

from app.usecase.municipal_social import MunicipalSocialEffect
from app.usecase.traffic import TrafficJob, TrafficRoad


@dataclass(frozen=True)
class MunicipalScenarioRequest:
    baseline_id: str
    region_id: str
    municipality_id: str
    kind: Literal["capacity", "closure", "lane_closure"]
    way_ids: list[int]
    edge_indices: list[int] = field(default_factory=list)


class MunicipalScenarios(Protocol):
    def baseline(self, region: str, municipality: str) -> "MunicipalTrafficBaseline": ...
    def submit(self, request: MunicipalScenarioRequest) -> TrafficJob: ...
    def get(self, identifier: str) -> TrafficJob: ...
    def cancel(self, identifier: str) -> TrafficJob: ...
    def effects(self, identifier: str) -> "MunicipalTrafficEffects": ...


@dataclass(frozen=True)
class MunicipalTrafficCorridor:
    way_id: int
    peak_ratio: float
    vehicle_hours: float
    length_km: float
    name: str = ""
    capacity_eligible: bool = True
    capacity_reason: str | None = None
    connected_parts: int = 1


@dataclass(frozen=True)
class MunicipalTrafficBaseline:
    baseline_id: str
    municipality_id: str
    corridors: list[MunicipalTrafficCorridor]
    roads: list[TrafficRoad]
    relative_gap: float
    source_bounds: list[float] | None
    artifact_sha256: str
    view: TrafficJob
    demand_zones: int | None = None
    demand_cell_km: float | None = None


@dataclass(frozen=True)
class MunicipalTrafficMetrics:
    vehicle_hours_on_local_edges: float
    overloaded_directed_edges: int
    unserved_departures: float


@dataclass(frozen=True)
class MunicipalTrafficEffects:
    municipality_id: str
    before: MunicipalTrafficMetrics
    after: MunicipalTrafficMetrics
    method: str = "edge_midpoint_and_synthetic_origin_membership_v1"
    social: tuple[MunicipalSocialEffect, ...] = ()
