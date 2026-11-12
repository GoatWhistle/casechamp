from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal, Protocol


@dataclass(frozen=True)
class TrafficHypothesis:
    source_place: str
    target_place: str
    rationale: str = ""


@dataclass(frozen=True)
class TrafficScope:
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


@dataclass(frozen=True)
class TrafficMetrics:
    vehicle_hours: float
    unserved_vehicles: float
    overloaded_edges: int
    relative_gap: float
    converged: bool
    mean_trip_minutes: float | None = None


@dataclass(frozen=True)
class TrafficRoad:
    way_id: int
    coordinates: list[list[float]]
    flow_before: float
    flow_after: float
    ratio_before: float | None
    ratio_after: float
    project: bool = False
    new_link: bool = False


@dataclass(frozen=True)
class TrafficIndexValue:
    region: str
    value: float
    population: int
    settlements: int
    normalization: float


@dataclass(frozen=True)
class TrafficIndexChange:
    region: str
    before: float
    after: float
    delta: float
    relative_percent: float | None
    population: int


@dataclass(frozen=True)
class TrafficAlternative:
    id: str
    kind: Literal["capacity", "connection", "closure", "opening", "package"]
    way_ids: list[int]
    length_km: float
    vehicle_hours_saved: float | None
    after: TrafficMetrics
    roads: list[TrafficRoad]
    indices: list[TrafficIndexChange] = field(default_factory=list)
    road_names: list[str] = field(default_factory=list)
    housing_clearance: bool | None = None
    structures: list[dict[str, object]] = field(default_factory=list)
    overload_increase: int = 0
    objective_before: float | None = None
    objective_after: float | None = None
    objective_gain: float | None = None
    objective_unit: str = ""


@dataclass(frozen=True)
class TrafficZone:
    longitude: float
    latitude: float
    population: float


@dataclass(frozen=True)
class TrafficJob:
    id: str
    scope: TrafficScope
    status: Literal["queued", "running", "completed", "failed", "cancelled"] = "queued"
    stage: str = "queued"
    completed: int = 0
    total: int = 1
    bounds: list[float] = field(default_factory=list)
    zones: list[TrafficZone] = field(default_factory=list)
    baseline: TrafficMetrics | None = None
    roads: list[TrafficRoad] = field(default_factory=list)
    alternatives: list[TrafficAlternative] = field(default_factory=list)
    indices: list[TrafficIndexValue] = field(default_factory=list)
    provenance: str = "{}"
    error: str = ""
    version: str = "network_development_targets_catboost_v4"


class TrafficSource(Protocol):
    def resolve(self, scope: TrafficScope) -> list[float]: ...
    def export(self, bounds: list[float], destination: Path) -> None: ...
    def inventory(self) -> str: ...


class TrafficStore(Protocol):
    def load(self) -> list[TrafficJob]: ...
    def save(self, job: TrafficJob) -> None: ...


class TrafficPort(Protocol):
    def submit(self, scope: TrafficScope) -> TrafficJob: ...
    def get(self, job_id: str) -> TrafficJob: ...
    def recent(self) -> list[TrafficJob]: ...
    def cancel(self, job_id: str) -> TrafficJob: ...
    def inventory(self) -> str: ...
