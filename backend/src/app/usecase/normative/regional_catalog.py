from dataclasses import dataclass
from typing import Protocol

from app.domain.errors import InvalidQuery
from app.domain.normative.model import Facility

ROAD_CRITERIA = frozenset({"N01", "N02", "N05", "N06", "N07", "N08"})

CATEGORIES = {
    "N01": "medical",
    "N02": "medical",
    "N03": "fire",
    "N04": "school",
    "N05": "mfc_candidate",
    "N06": "employment_candidate",
    "N07": "library",
    "N08": "bus_station",
    "N09": "stop",
}


@dataclass(frozen=True, slots=True)
class RegionalCatalog:
    region_id: str
    region_name: str
    criterion_id: str
    category: str
    facilities: list[Facility]
    candidate_count: int
    road_measurement_available: bool = False
    walking_measurement_available: bool = False
    emergency_measurement_available: bool = False
    calculation_available: bool = False
    profile_verification: str = "unconfirmed"


class RegionalCatalogRepository(Protocol):
    def region_name(self, region_id: str) -> str | None: ...
    def walking_available(self, region_id: str) -> bool: ...
    def candidates(self, region_id: str, category: str) -> list[Facility]: ...
    def routing_candidates(self, category: str) -> list[Facility]: ...


class RegionalCatalogQueries:
    def __init__(self, repository: RegionalCatalogRepository) -> None:
        self.repository = repository

    def scope(self, region_id: str, criterion_id: str) -> tuple[str, str]:
        category = CATEGORIES.get(criterion_id)
        name = self.repository.region_name(region_id)
        if category is None or name is None:
            raise InvalidQuery("Unknown regional service catalog")
        return category, name

    def catalog(self, region_id: str, criterion_id: str, *, cross_region: bool = False) -> RegionalCatalog:
        category, name = self.scope(region_id, criterion_id)
        facilities = (self.repository.routing_candidates(category) if cross_region
                      else self.repository.candidates(region_id, category))
        return RegionalCatalog(
            region_id,
            name,
            criterion_id,
            category,
            facilities,
            len(facilities),
            road_measurement_available=criterion_id in ROAD_CRITERIA,
            walking_measurement_available=criterion_id in {"N04", "N09"}
            and self.repository.walking_available(region_id),
            emergency_measurement_available=criterion_id == "N03",
        )
