from dataclasses import dataclass
from typing import Protocol

from app.domain.transit_journey import TransitConnection


@dataclass(frozen=True)
class TransitStop:
    id: str
    name: str
    region_id: str
    region_code: str
    latitude: float | None
    longitude: float | None
    coordinate_status: str
    coordinate_source_url: str
    coordinate_source_sha256: str


@dataclass(frozen=True)
class TransitSnapshot:
    id: str
    source_date: str
    source_url: str
    input_sha256: str
    clock_basis: str
    timezone_verified: bool
    coverage_complete: bool
    operating_service_verified: bool
    stops: list[TransitStop]
    connections: list[TransitConnection]


class TransitCatalog(Protocol):
    def latest(self) -> TransitSnapshot: ...
