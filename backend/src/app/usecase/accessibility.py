from dataclasses import dataclass
from typing import Protocol

from app.domain.accessibility import HALF_LIVES
from app.domain.errors import DataUnavailable, InvalidQuery, RegionNotFound
from app.usecase.interface import AtlasRepository


@dataclass(frozen=True, slots=True)
class AccessibilityRun:
    run_id: str
    created_at: str
    model_version: str
    source_model: str
    source_artifact: str
    normalization: float
    normalization_kind: str
    regions: int
    markets: int
    point_count: int
    frequency_status: str
    assumptions: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class AccessibilityRow:
    season: str
    half_life: int
    previous: float
    potential: float
    delta: float
    without_air: float
    without_rail: float
    without_water: float
    population: int
    population_coverage: float
    scheduled_index: float | None = None


@dataclass(frozen=True, slots=True)
class FrequencyCoverage:
    season: str
    mode: str
    source: str
    total: int
    known: int


@dataclass(frozen=True, slots=True)
class AccessibilityComparison:
    region_id: str
    source_current: bool
    run: AccessibilityRun
    rows: tuple[AccessibilityRow, ...]
    frequencies: tuple[FrequencyCoverage, ...]


class AccessibilityRepository(Protocol):
    def comparison(self, region_id: str, half_life: int) -> AccessibilityComparison: ...


class AccessibilityQueries:
    def __init__(self, repository: AccessibilityRepository, atlas: AtlasRepository) -> None:
        self.repository = repository
        self.atlas = atlas

    def compare(self, region_id: str, half_life: int) -> AccessibilityComparison:
        if half_life not in HALF_LIVES:
            raise InvalidQuery("Half-life must be 2, 4 or 8 hours")
        if not any(row.id == region_id for row in self.atlas.regions()):
            raise RegionNotFound()
        result = self.repository.comparison(region_id, half_life)
        if {row.season for row in result.rows} != {"summer", "winter"} or len(result.rows) != 2:
            raise DataUnavailable("Accessibility comparison is incomplete")
        return result
