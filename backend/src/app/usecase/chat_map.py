from dataclasses import dataclass
from typing import Literal

from app.domain.transport import NetworkMode, Season
from app.usecase.regions import RegionQueries
from app.usecase.settlements import SettlementQueries

MapAction = Literal["focus", "reset", "zoom_in", "zoom_out"]


@dataclass(frozen=True, slots=True)
class SettlementMapTarget:
    id: str
    name: str
    region_id: str
    longitude: float
    latitude: float


@dataclass(frozen=True, slots=True)
class ChatMapCommand:
    action: MapAction | Literal["focus_settlement"]
    region_ids: tuple[str, ...]
    settlement: SettlementMapTarget | None = None


class ChatMap:
    def __init__(self, regions: RegionQueries, settlements: SettlementQueries | None = None) -> None:
        self._regions = regions
        self._settlements = settlements

    def settlement(self, settlement_id: str) -> ChatMapCommand:
        if self._settlements is None:
            raise ValueError("Settlement map focus is unavailable")
        point = self._settlements.location(settlement_id)
        return ChatMapCommand(
            "focus_settlement", (point.region_id,),
            SettlementMapTarget(point.id, point.name, point.region_id, point.lon, point.lat),
        )

    def command(self, action: MapAction, region_ids: list[str]) -> ChatMapCommand:
        ids = tuple(dict.fromkeys(region_ids))
        if action != "focus":
            if ids:
                raise ValueError("Only focus accepts region identifiers")
            return ChatMapCommand(action, ())
        if not 1 <= len(ids) <= 30:
            raise ValueError("Focus requires between 1 and 30 regions")
        available = {
            row.id for row in self._regions.summaries(Season.SUMMER, NetworkMode.ROAD)
            if row.has_geometry
        }
        if set(ids) - available:
            raise ValueError("Unknown region or missing geometry; search or list regions first")
        return ChatMapCommand(action, ids)
