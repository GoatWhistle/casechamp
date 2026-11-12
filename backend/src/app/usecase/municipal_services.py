from collections.abc import Callable
from concurrent.futures import Future, ThreadPoolExecutor
from dataclasses import replace
from threading import Lock
from time import monotonic

from app.domain.errors import DataUnavailable
from app.domain.municipal_metrics import MunicipalObservation, municipal_contains
from app.domain.normative.index import reference_index_values
from app.domain.normative.model import AccessRow, Facility, Origin
from app.domain.normative.scenario_index import scenario_policy
from app.usecase.municipal_service_models import (
    MunicipalNormativeValue,
    merge_municipal_values,
    municipal_origins,
    municipal_pending,
)
from app.usecase.municipalities import Municipality
from app.usecase.normative.interface import NormativeRouting
from app.usecase.normative.regional_catalog import RegionalCatalogQueries
from app.usecase.normative.regional_models import RegionalWalkingModels

__all__ = ["MunicipalNormativeValue", "MunicipalServiceQueries"]


class MunicipalServiceQueries:
    def __init__(
        self,
        catalog: RegionalCatalogQueries,
        road: NormativeRouting | None,
        walking: RegionalWalkingModels | None,
        walking_origins: Callable[[str], list[Origin]] | None = None,
        published: Callable[[Municipality], list[MunicipalNormativeValue]] | None = None,
        version: Callable[[Municipality], str] | None = None,
    ) -> None:
        self.catalog = catalog
        self.road = road
        self.walking = walking
        self.walking_origins = walking_origins
        self.published = published
        self.version = version
        self._executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="municipal-access")
        self._lock = Lock()
        self._progress: dict[tuple[str, str, str, str], list[MunicipalNormativeValue]] = {}
        self._jobs: dict[
            tuple[str, str, str, str], tuple[float, Future[list[MunicipalNormativeValue]]]
        ] = {}

    def close(self) -> None:
        self._executor.shutdown(wait=True, cancel_futures=True)

    def values(
        self, municipality: Municipality, points: list[MunicipalObservation]
    ) -> list[MunicipalNormativeValue]:
        published = self.published(municipality) if self.published else []

        if {"N01", "N02", "N04"}.issubset({item.criterion_id for item in published}):
            return merge_municipal_values(published, [])
        key = (
            municipality.region_id,
            municipality.id,
            municipality.source_sha256,
            self.version(municipality) if self.version else "",
        )
        with self._lock:
            job = self._jobs.get(key)
            retry = 300.0
            if (
                job
                and job[1].done()
                and (
                    job[1].exception() is not None
                    or any(item.status == "unavailable" for item in job[1].result())
                )
            ):
                retry = 30.0
            if job and job[1].done() and monotonic() - job[0] > retry:
                del self._jobs[key]
                self._progress.pop(key, None)
                job = None
            if job is None:
                completed = sorted(
                    (stamp, item) for item, (stamp, future) in self._jobs.items() if future.done()
                )
                for _, item in completed[: max(0, len(self._jobs) - 15)]:
                    del self._jobs[item]
                    self._progress.pop(item, None)
                if len(self._jobs) >= 16:
                    return merge_municipal_values(
                        published,
                        [
                            MunicipalNormativeValue(key, reason="municipal_calculation_queue_full")
                            for key in ("N01", "N02", "N04")
                        ],
                    )
                job = (
                    monotonic(),
                    self._executor.submit(self._calculate, municipality, points, key),
                )
                self._jobs[key] = job
            progress = list(self._progress.get(key, []))
        if not job[1].done():
            known = {item.criterion_id: item for item in progress}
            return merge_municipal_values(
                published,
                [
                    known.get(
                        criterion,
                        municipal_pending(criterion),
                    )
                    for criterion in ("N04", "N01", "N02")
                ],
            )
        if job[1].exception() is not None:
            return merge_municipal_values(
                published,
                [
                    MunicipalNormativeValue(criterion, reason="municipal_calculation_failed")
                    for criterion in ("N04", "N01", "N02")
                ],
            )
        return merge_municipal_values(published, job[1].result())

    def _calculate(
        self,
        municipality: Municipality,
        points: list[MunicipalObservation],
        key: tuple[str, str, str, str],
    ) -> list[MunicipalNormativeValue]:
        origins = municipal_origins(points)
        results = []
        medical_rows: list[AccessRow] | None = None
        medical_facilities: list[Facility] | None = None
        for criterion in ("N04", "N01", "N02"):
            policy = scenario_policy(criterion)
            entry = MunicipalNormativeValue(
                criterion,
                unit=policy.unit,
                mode=policy.mode,
                thresholds=policy.thresholds,
                definition_sha256=policy.definition_sha256,
                reference_points=len(origins),
            )
            try:
                catalog = self.catalog.catalog(municipality.region_id, criterion)
                routing = (
                    (self.walking.for_region(municipality.region_id) if self.walking else None)
                    if criterion == "N04"
                    else self.road
                )
                selected_origins = origins
                if criterion == "N04" and routing is not None:
                    if self.walking_origins is None:
                        raise DataUnavailable("No sourced residential reference origins configured")
                    vertices = [
                        point
                        for polygon in municipality.coordinates
                        for ring in polygon
                        for point in ring
                    ]
                    west, east = min(p[0] for p in vertices), max(p[0] for p in vertices)
                    south, north = min(p[1] for p in vertices), max(p[1] for p in vertices)
                    selected_origins = [
                        origin
                        for origin in self.walking_origins(routing.revision)
                        if origin.longitude is not None
                        and origin.latitude is not None
                        and south <= origin.latitude <= north
                        and any(
                            west <= origin.longitude + shift <= east for shift in (-360, 0, 360)
                        )
                        and municipal_contains(
                            origin.longitude, origin.latitude, municipality.coordinates
                        )
                    ]
                    entry = replace(
                        entry,
                        origin_kind="residential_reference_points",
                        reference_points=len(selected_origins),
                    )
                if not selected_origins:
                    results.append(replace(entry, reason="municipal_reference_points_missing"))
                    continue
                if not catalog.facilities:
                    results.append(replace(entry, reason="municipal_service_facilities_missing"))
                    continue
                if routing is None:
                    results.append(
                        replace(
                            entry,
                            reason="municipal_walking_network_missing"
                            if criterion == "N04"
                            else "municipal_road_network_missing",
                        )
                    )
                    continue
                rows = (
                    medical_rows
                    if criterion == "N02"
                    and medical_rows is not None
                    and medical_facilities == catalog.facilities
                    else routing.evaluate(
                        selected_origins, catalog.facilities, policy.thresholds[0], []
                    )
                )
                if criterion == "N01":
                    medical_rows = rows
                    medical_facilities = catalog.facilities
                costs = [
                    row.distance_metres if policy.unit == "metres" else row.minutes for row in rows
                ]
                finite = [cost for cost in costs if cost is not None]
                values = reference_index_values(rows, policy.unit, policy.thresholds)
                results.append(
                    replace(
                        entry,
                        value=values[0].point_share_percent if finite else None,
                        status="available" if finite else "unavailable",
                        reason="conditional_known_objects"
                        if finite
                        else "municipal_routes_unresolved",
                        values=tuple(values),
                        mean_travel=sum(finite) / len(finite) if finite else None,
                        measured_points=len(finite),
                        facilities=len(catalog.facilities),
                        model_revision=routing.revision,
                        source_urls=tuple(
                            sorted({facility.source_url for facility in catalog.facilities})
                        ),
                    )
                )
            except DataUnavailable:
                results.append(
                    replace(
                        entry,
                        reason="municipal_walking_network_missing"
                        if criterion == "N04"
                        else "municipal_routing_unavailable",
                    )
                )
            finally:
                with self._lock:
                    self._progress[key] = list(results)
        return results
