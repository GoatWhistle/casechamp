from dataclasses import dataclass
from typing import Literal

from app.domain.normative.fire import FireProfile
from app.domain.normative.model import AccessRow, Criterion, Facility

MODEL_REVISION = "normative-v8"
TRACE_MODEL_REVISIONS = frozenset(
    {"normative-v3", "normative-v4", "normative-v5", "normative-v6", "normative-v7", MODEL_REVISION}
)
RouteStage = Literal["baseline", "scenario"]


@dataclass(frozen=True, slots=True)
class RouteGeometry:
    network_coordinates: list[tuple[float, float]]
    approaches: list[list[tuple[float, float]]]
    minutes: float | None
    distance_metres: float | None


@dataclass(frozen=True, slots=True)
class NormativeRoute:
    run_id: str
    origin_id: str
    facility_id: str
    stage: RouteStage
    graph_revision: str
    model_revision: str
    geometry: RouteGeometry


@dataclass(frozen=True, slots=True)
class RouteContext:
    criterion: Criterion
    graph_revision: str
    model_revision: str
    origin: AccessRow
    facility: Facility | None
    closed_way_ids: list[int]
    fire_profile: FireProfile | None = None
