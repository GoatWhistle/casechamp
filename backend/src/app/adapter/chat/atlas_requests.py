from dataclasses import field
from typing import Literal

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from app.usecase.chat_artifacts import ComparisonMetric
from app.usecase.chat_map import MapAction


@dataclass(config=ConfigDict(extra="forbid"))
class RegionsQuery:
    kind: Literal["regions"]
    region_ids: list[str] = field(default_factory=list)
    metric: ComparisonMetric | None = None
    limit: int = 8
    descending: bool = False


@dataclass(config=ConfigDict(extra="forbid"))
class PlacesQuery:
    kind: Literal["places"]
    query: str


@dataclass(config=ConfigDict(extra="forbid"))
class SettlementsQuery:
    kind: Literal["settlements"]
    region_id: str
    query: str = ""


@dataclass(config=ConfigDict(extra="forbid"))
class LinksQuery:
    kind: Literal["links"]
    region_id: str
    offset: int = 0


@dataclass(config=ConfigDict(extra="forbid"))
class ReferenceQuery:
    kind: Literal["sources", "capabilities"]


@dataclass(config=ConfigDict(extra="forbid"))
class SensitivityQuery:
    kind: Literal["sensitivity"]
    region_id: str


type AtlasQuery = (
    RegionsQuery | PlacesQuery | SettlementsQuery | LinksQuery | ReferenceQuery | SensitivityQuery
)


@dataclass(config=ConfigDict(extra="forbid"))
class ChartPresentation:
    kind: Literal["chart"]
    table_id: str
    x: str
    y: str


@dataclass(config=ConfigDict(extra="forbid"))
class MapPresentation:
    kind: Literal["map"]
    action: MapAction
    region_ids: list[str] = field(default_factory=list)


@dataclass(config=ConfigDict(extra="forbid"))
class SettlementPresentation:
    kind: Literal["settlement"]
    settlement_id: str


@dataclass(config=ConfigDict(extra="forbid"))
class RoadPresentation:
    kind: Literal["road"]
    way_ids: list[int] = field(default_factory=list)
    selection_ids: list[str] = field(default_factory=list)


type AtlasPresentation = ChartPresentation | MapPresentation | SettlementPresentation | RoadPresentation
