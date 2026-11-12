from dataclasses import dataclass
from typing import Protocol

from app.domain.errors import DataUnavailable, RegionNotFound
from app.usecase.interface import AtlasRepository

type MunicipalCoordinates = list[list[list[tuple[float, float]]]]


@dataclass(frozen=True, slots=True)
class Municipality:
    id: str
    region_id: str
    name: str
    admin_level: int
    coordinates: MunicipalCoordinates
    source_url: str
    observed_at: str
    source_sha256: str
    region_assignment: str
    region_overlap_fraction: float


class MunicipalRepository(Protocol):
    def boundaries(self, region_id: str) -> list[Municipality]: ...


@dataclass(frozen=True, slots=True)
class MunicipalCollection:
    region_id: str
    items: list[Municipality]
    reason: str | None


class MunicipalityQueries:
    def __init__(self, repository: MunicipalRepository, atlas: AtlasRepository) -> None:
        self.repository = repository
        self.atlas = atlas

    def run(self, region_id: str) -> MunicipalCollection:
        if region_id not in {region.id for region in self.atlas.regions()}:
            raise RegionNotFound()
        try:
            items = self.repository.boundaries(region_id)
        except DataUnavailable:
            return MunicipalCollection(region_id, [], "municipal_storage_unavailable")
        return MunicipalCollection(
            region_id,
            items,
            "partial_source_coverage" if items else "municipal_geometry_not_imported",
        )
