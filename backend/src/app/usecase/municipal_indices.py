from collections import OrderedDict
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from threading import Lock
from time import monotonic
from typing import Protocol

from app.domain.errors import InvalidQuery
from app.domain.municipal_metrics import (
    MunicipalMetric,
    MunicipalObservation,
    aggregate_metric,
    municipal_points,
)
from app.usecase.municipal_services import MunicipalNormativeValue, MunicipalServiceQueries
from app.usecase.municipalities import Municipality, MunicipalityQueries


@dataclass(frozen=True, slots=True)
class MunicipalIndexSource:
    points: list[MunicipalObservation]
    model_version: str | None
    artifact_version: str | None
    source_table: str


class MunicipalIndexRepository(Protocol):
    def points(self, region_id: str, season: str) -> MunicipalIndexSource: ...


@dataclass(frozen=True, slots=True)
class MunicipalityIndices:
    region_id: str
    municipality_id: str
    name: str
    season: str
    connectivity: MunicipalMetric
    region_connectivity: MunicipalMetric
    metrics: list[MunicipalMetric]
    normative: list[MunicipalNormativeValue]
    method: str
    model_version: str | None
    artifact_version: str | None
    source_table: str
    computed_at: str
    boundary_source_url: str
    boundary_source_sha256: str


class MunicipalIndexQueries:
    def __init__(
        self,
        municipalities: MunicipalityQueries,
        repository: MunicipalIndexRepository,
        services: MunicipalServiceQueries | None = None,
    ) -> None:
        self.municipalities = municipalities
        self.repository = repository
        self.services = services
        self._cache: OrderedDict[
            tuple[str, str, str],
            tuple[float, MunicipalityIndices, Municipality, list[MunicipalObservation]],
        ] = OrderedDict()
        self._lock = Lock()

    def run(
        self, region_id: str, municipality_id: str, season: str = "road"
    ) -> MunicipalityIndices:
        if season not in {"road", "summer", "winter"}:
            raise InvalidQuery("Invalid municipal index season")
        key = (region_id, municipality_id, season)
        with self._lock:
            cached = self._cache.get(key)
            if cached and monotonic() - cached[0] < 60:
                self._cache.move_to_end(key)
                result, cached_municipality, points = cached[1:]
                return (
                    replace(result, normative=self.services.values(cached_municipality, points))
                    if self.services
                    else result
                )
        municipality = next(
            (
                item
                for item in self.municipalities.run(region_id).items
                if item.id == municipality_id
            ),
            None,
        )
        if municipality is None:
            raise InvalidQuery("Municipality is not available in this region")
        source = self.repository.points(region_id, season)
        points = municipal_points(source.points, municipality.coordinates)
        service_points = (
            points
            if season == "road"
            else municipal_points(
                self.repository.points(region_id, "road").points, municipality.coordinates
            )
        )
        result = MunicipalityIndices(
            region_id,
            municipality_id,
            municipality.name,
            season,
            aggregate_metric(points, "hansen_idx", "index_points"),
            aggregate_metric(source.points, "hansen_idx", "index_points"),
            [
                aggregate_metric(points, metric, unit)
                for metric, unit in (
                    ("hansen_1h", "weighted_population"),
                    ("hansen_2h", "weighted_population"),
                    ("hansen_4h", "weighted_population"),
                    ("remoteness_ca", "ratio"),
                    ("aria", "index_points"),
                    ("harris", "index_points"),
                    ("t_city50k_best_h", "hours"),
                    ("rai_2km", "ratio"),
                )
            ],
            [MunicipalNormativeValue(f"N{index:02}") for index in range(1, 10)],
            "population_weighted_source_points_in_original_municipal_polygon_v1",
            source.model_version,
            source.artifact_version,
            source.source_table,
            datetime.now(UTC).isoformat(),
            municipality.source_url,
            municipality.source_sha256,
        )
        with self._lock:
            self._cache[key] = (monotonic(), result, municipality, service_points)
            self._cache.move_to_end(key)
            while len(self._cache) > 128:
                self._cache.popitem(last=False)
        if self.services:
            return replace(result, normative=self.services.values(municipality, service_points))
        return result
