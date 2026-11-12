from math import isfinite
from typing import Protocol

from app.domain.appraisal_inputs import ProjectAssumptions
from app.domain.appraisal_validation import validate_project
from app.domain.errors import DataUnavailable, InvalidQuery, RegionNotFound
from app.domain.road_economics import MoneyAssumptions
from app.usecase.closure_matching import matching_closure_jobs
from app.usecase.graph_snapshot import GraphModelInfo
from app.usecase.interface import AtlasRepository
from app.usecase.road_geometry import RoadGeometry, RoadGeometrySource
from app.usecase.road_profile_validation import validate_changes
from app.usecase.road_records import (
    GraphLocation,
    RoadAddition,
    RoadChange,
    RoadJob,
    RoadResult,
    RoadSegment,
    RoadView,
    SettlementEffect,
)
from app.usecase.selected_road_view import selected_view
from app.usecase.transport_links import LinkChange, PlaceName, TransportLink, validate_links

__all__ = [
    "GraphLocation",
    "RoadAddition",
    "RoadChange",
    "RoadGraph",
    "RoadGraphPort",
    "RoadJob",
    "RoadResult",
    "RoadSegment",
    "RoadView",
    "RoadViewSource",
    "SettlementEffect",
]


class RoadGraphPort(Protocol):
    @property
    def metadata(self) -> GraphModelInfo: ...
    def markets(self) -> list[str]: ...
    def locations(self, query: str, region_id: str | None) -> list[GraphLocation]: ...
    def view(self, bounds: tuple[float, float, float, float], zoom: float) -> RoadView: ...
    def submit(
        self,
        region_id: str,
        region: str,
        scenario: str,
        changes: list[RoadChange],
        links: list[LinkChange] | None = None,
        *,
        queue: bool = False,
        appraisal: ProjectAssumptions | None = None,
    ) -> RoadJob: ...
    def transport_links(
        self, network: str, scenario: str, place: str, mode: str | None
    ) -> list[TransportLink]: ...
    def place_names(self, ids: list[str]) -> list[PlaceName]: ...
    def submit_addition(
        self,
        region_id: str,
        region: str,
        addition: RoadAddition,
        money: MoneyAssumptions | None,
        appraisal: ProjectAssumptions | None = None,
    ) -> RoadJob: ...
    def recent(self, limit: int | None = 20) -> list[RoadJob]: ...
    def job(self, job_id: str) -> RoadJob: ...
    def cancel(self, job_id: str) -> RoadJob: ...


class RoadViewSource(Protocol):
    def view(self, bounds: tuple[float, float, float, float], zoom: float) -> RoadView: ...


class RoadGraph:
    def __init__(
        self,
        engine: RoadGraphPort | None,
        atlas: AtlasRepository,
        view_source: RoadViewSource | None = None,
        geometry_source: RoadGeometrySource | None = None,
    ) -> None:
        self._engine = engine
        self.atlas = atlas
        self.view_source = view_source
        self.geometry_source = geometry_source

    @property
    def engine(self) -> RoadGraphPort:
        if self._engine is None:
            raise DataUnavailable("GRAPH_DIR is not configured")
        return self._engine

    def markets(self) -> list[str]:
        return self.engine.markets()

    def model_info(self) -> GraphModelInfo:
        return self.engine.metadata

    def locations(self, query: str, region_id: str | None = None) -> list[GraphLocation]:
        if not 2 <= len(query.strip()) <= 100:
            raise InvalidQuery("Place query must contain between 2 and 100 characters")
        return self.engine.locations(query.strip(), region_id)

    def recent(self) -> list[RoadJob]:
        return self.engine.recent()

    def closure_jobs(self, way_ids: list[int], version: str) -> list[RoadJob]:
        return matching_closure_jobs(self.engine.recent(limit=None), way_ids, version)

    def submit_closure(
        self, way_ids: list[int], region_ids: list[str], version: str
    ) -> list[RoadJob]:
        if version != self.model_info().version:
            raise InvalidQuery("Closure belongs to a different graph version")
        ids = sorted(set(way_ids))
        if not 1 <= len(ids) <= 20000:
            raise InvalidQuery("Select between 1 and 20000 road ways")
        regions = {r.id: r for r in self.atlas.regions()}
        if any(key not in regions for key in region_ids):
            raise RegionNotFound()
        existing = {
            job.region_id: job
            for job in self.closure_jobs(ids, version)
            if job.status in {"queued", "running", "completed"}
        }
        changes = [RoadChange(way, 0) for way in ids]
        return [
            existing[key]
            if key in existing
            else self.engine.submit(
                key,
                regions[key].name,
                "road",
                changes,
                queue=True,
            )
            for key in dict.fromkeys(region_ids)
        ]

    def geometry(self, way_ids: list[int]) -> RoadGeometry:
        if self.geometry_source is None:
            raise DataUnavailable("Road scenario geometry is not configured")
        return self.geometry_source.geometry(way_ids)

    def view(
        self,
        west: float,
        south: float,
        east: float,
        north: float,
        zoom: float,
        region_id: str | None = None,
    ) -> RoadView:
        if not all(isfinite(v) for v in (west, south, east, north, zoom)):
            raise InvalidQuery()
        if not (-180 <= west < east <= 180 and -85 <= south < north <= 85 and 0 <= zoom <= 22):
            raise InvalidQuery()
        source = self.view_source if self.view_source is not None else self.engine
        if region_id is not None:
            return selected_view(source, self.atlas, (west, south, east, north), zoom, region_id)
        return source.view((west, south, east, north), zoom)

    def transport_links(
        self, network: str, scenario: str, place: str, mode: str | None = None
    ) -> list[TransportLink]:
        if network not in {"intercity", "local"} or scenario not in {"road", "summer", "winter"}:
            raise InvalidQuery("Сеть: intercity или local; сценарий: road, summer или winter")
        if not 2 <= len(place.strip()) <= 100:
            raise InvalidQuery("Укажите город, населённый пункт или регион")
        return self.engine.transport_links(network, scenario, place.strip(), mode)

    def place_names(self, ids: list[str]) -> list[PlaceName]:
        if not 1 <= len(ids) <= 60:
            raise InvalidQuery("Укажите от 1 до 60 ID населённых пунктов")
        return self.engine.place_names(sorted(set(ids)))

    def submit(
        self,
        region_id: str,
        scenario: str,
        changes: list[RoadChange],
        links: list[LinkChange] | None = None,
        *,
        queue: bool = False,
        appraisal: ProjectAssumptions | None = None,
    ) -> RoadJob:
        if appraisal is not None:
            validate_project(appraisal)
        links = links or []
        if scenario not in {"road", "summer", "winter"} or len(changes) > 50 or len(links) > 30:
            raise InvalidQuery()
        if not changes and not links:
            raise InvalidQuery("Укажите изменения дорог или связей")
        validate_links(links)
        if len({c.way_id for c in changes}) != len(changes):
            raise InvalidQuery("Duplicate road identifiers")
        validate_changes(changes)
        region = next((r for r in self.atlas.regions() if r.id == region_id), None)
        if region is None:
            raise RegionNotFound()
        return self.engine.submit(
            region_id, region.name, scenario, changes, links, queue=queue, appraisal=appraisal
        )

    def add_connection(
        self,
        region_id: str,
        addition: RoadAddition,
        money: MoneyAssumptions | None = None,
        appraisal: ProjectAssumptions | None = None,
    ) -> RoadJob:
        if appraisal is not None:
            validate_project(appraisal)
            if money is not None:
                raise InvalidQuery("Choose either legacy money or project appraisal")
        if (
            addition.source_node < 0
            or addition.target_node < 0
            or addition.source_node == addition.target_node
            or not isfinite(addition.travel_hours)
            or not 0 < addition.travel_hours <= 72
        ):
            raise InvalidQuery("Specify two distinct graph nodes and a travel time in (0,72] hours")
        if money and any(
            not isfinite(v) or v < 0
            for v in (
                money.trips_per_year,
                money.rub_per_hour,
                money.capital_cost_rub,
                money.annual_operating_cost_rub,
            )
        ):
            raise InvalidQuery("Economic assumptions must be finite and nonnegative")
        region = next((r for r in self.atlas.regions() if r.id == region_id), None)
        if region is None:
            raise RegionNotFound()
        return self.engine.submit_addition(region_id, region.name, addition, money, appraisal)

    def job(self, job_id: str) -> RoadJob:
        return self.engine.job(job_id)

    def cancel(self, job_id: str) -> RoadJob:
        return self.engine.cancel(job_id)
