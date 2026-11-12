from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from pathlib import Path
from threading import Event, Lock
from uuid import uuid4

from app.adapter.log.stdlib import StdlibLogger
from app.adapter.road_graph.addition import addition_job, locate_addition
from app.adapter.road_graph.appraisal import AppraisalRouting
from app.adapter.road_graph.baselines import BaselineCache
from app.adapter.road_graph.closure_validity import road_job_view
from app.adapter.road_graph.data import GraphData
from app.adapter.road_graph.delta import DeltaCalculation
from app.adapter.road_graph.delta_base import DeltaBase
from app.adapter.road_graph.full_calculation import FullCalculation
from app.adapter.road_graph.routing import GraphRouting
from app.adapter.road_graph.shortest_paths import ShortestPaths
from app.adapter.road_graph.transport_catalog import TransportCatalog
from app.domain.appraisal import AppraisalReport
from app.domain.appraisal_inputs import ProjectAssumptions
from app.domain.errors import DataUnavailable, InvalidQuery
from app.domain.road_economics import MoneyAssumptions
from app.usecase.graph_snapshot import GraphSnapshot
from app.usecase.road_graph import (
    GraphLocation,
    RoadAddition,
    RoadChange,
    RoadJob,
    RoadResult,
    RoadView,
)
from app.usecase.road_job_store import RoadJobStore
from app.usecase.transport_links import LinkChange, PlaceName, TransportLink


class RoadJobs:
    def __init__(
        self, root: Path, snapshot: GraphSnapshot, store: RoadJobStore, workers: int = 1
    ) -> None:
        self.data = GraphData(root, snapshot)
        self.metadata = self.data.model_info()
        self.paths = ShortestPaths(workers)
        self.routing = GraphRouting(self.data, self.paths)
        self.catalog = TransportCatalog(self.data, self.routing)
        self.cache = BaselineCache(root, snapshot.revision, self.data.road_cost_model)
        self.delta = DeltaCalculation(DeltaBase(self.data, self.paths))
        self.delta.base.prepare()
        self.pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="road-calculation")
        self.lock, self.store = Lock(), store
        self.jobs = {
            key: replace(job, status="cancelled") if job.status in {"queued", "running"} else job
            for key, job in store.load().items()
        }
        self.stops = {key: Event() for key in self.jobs}
        self.baselines: dict[tuple[str, str], float] = {}

    def markets(self) -> list[str]:
        return [str(row[0]) for row in self.data.read("cities")]

    def locations(self, query: str, region_id: str | None) -> list[GraphLocation]:
        return self.data.locations(query, region_id)

    def view(self, bounds: tuple[float, float, float, float], zoom: float) -> RoadView:
        return self.data.view(bounds, zoom)

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
    ) -> RoadJob:
        self.data.region_name(region_id)
        self.data.indices_for([c.way_id for c in changes])
        links = self.routing.prepare_links(scenario, links or [])
        key = (region_id, scenario, changes, links, appraisal)
        with self.lock:
            for job in self.jobs.values():
                if job.status in {"queued", "running"}:
                    if (
                        job.region_id,
                        job.scenario,
                        job.changes,
                        job.links,
                        job.appraisal_assumptions,
                    ) == key:
                        return job
                    if not queue:
                        raise InvalidQuery("A calculation is already running; wait or cancel it")
            job = RoadJob(
                uuid4().hex,
                region_id,
                region,
                scenario,
                changes,
                "queued",
                0,
                360,
                self.data.version,
                appraisal_assumptions=appraisal,
                links=links,
            )
            self.store.save(job)
            self.jobs[job.id] = job
            self.stops[job.id] = Event()
        self.pool.submit(self.run, job)
        return job

    def submit_addition(
        self,
        region_id: str,
        region: str,
        addition: RoadAddition,
        money: MoneyAssumptions | None,
        appraisal: ProjectAssumptions | None = None,
    ) -> RoadJob:
        self.data.region_name(region_id)
        addition = locate_addition(self.data, addition)
        with self.lock:
            for existing in self.jobs.values():
                if existing.status in {"queued", "running"}:
                    if (
                        existing.region_id,
                        existing.addition,
                        existing.money_assumptions,
                        existing.appraisal_assumptions,
                    ) == (
                        region_id,
                        addition,
                        money,
                        appraisal,
                    ):
                        return existing
                    raise InvalidQuery("A calculation is already running; wait or cancel it")
            job = addition_job(region_id, region, addition, money, appraisal, self.data.version)
            self.store.save(job)
            self.jobs[job.id] = job
            self.stops[job.id] = Event()
        self.pool.submit(self.run, job)
        return job

    def transport_links(
        self, network: str, scenario: str, place: str, mode: str | None
    ) -> list[TransportLink]:
        return self.catalog.links(network, scenario, place, mode)

    def place_names(self, ids: list[str]) -> list[PlaceName]:
        return self.catalog.place_names(ids)

    def recent(self, limit: int | None = 20) -> list[RoadJob]:
        with self.lock:
            return list(reversed(list(self.jobs.values())))[:limit]

    def job(self, job_id: str) -> RoadJob:
        with self.lock:
            if job_id not in self.jobs:
                raise InvalidQuery("Unknown calculation")
            job = self.jobs[job_id]
        return road_job_view(job, self.data.attachment_audit)

    def cancel(self, job_id: str) -> RoadJob:
        self.job(job_id)
        self.stops[job_id].set()
        return self.job(job_id)

    def update(
        self,
        job_id: str,
        *,
        status: str,
        completed: int,
        result: RoadResult | None = None,
        error: str | None = None,
        appraisal_result: AppraisalReport | None = None,
    ) -> None:
        with self.lock:
            self.jobs[job_id] = replace(
                self.jobs[job_id],
                status=status,
                completed=completed,
                result=result,
                error=error,
                appraisal_result=appraisal_result,
            )
            if status in {"completed", "cancelled", "failed"}:
                try:
                    self.store.save(self.jobs[job_id])
                except DataUnavailable as storage_error:
                    self.jobs[job_id] = replace(self.jobs[job_id], error=error or "storage_pending")
                    StdlibLogger("road_graph").error(
                        "calculation_storage_failed", exc=storage_error, job_id=job_id
                    )

    def run(self, job: RoadJob) -> None:
        def progress(value: int) -> None:
            if self.stops[job.id].is_set():
                raise InterruptedError()
            self.update(job.id, status="running", completed=value)

        try:
            progress(0)
            region = self.data.region_name(job.region_id)
            appraisal = (
                AppraisalRouting(job.appraisal_assumptions) if job.appraisal_assumptions else None
            )
            if job.addition:
                result = self.delta.calculate(
                    region, job.addition, job.money_assumptions, progress, appraisal
                )
                self.update(
                    job.id,
                    status="completed",
                    completed=5,
                    result=result,
                    appraisal_result=appraisal.result() if appraisal else None,
                )
                return
            result = FullCalculation(self.data, self.routing, self.cache, self.baselines).calculate(
                job, region, progress, appraisal
            )
            self.update(
                job.id,
                status="completed",
                completed=360,
                result=result,
                appraisal_result=appraisal.result() if appraisal else None,
            )
        except InterruptedError:
            self.update(job.id, status="cancelled", completed=self.job(job.id).completed)
        except Exception as error:  # noqa: BLE001 - worker boundary records failure and logs the cause
            StdlibLogger("road_graph").error("calculation_failed", exc=error, job_id=job.id)
            self.update(
                job.id,
                status="failed",
                completed=self.job(job.id).completed,
                error="baseline_mismatch"
                if str(error) == "baseline_mismatch"
                else "calculation_failed",
            )

    def close(self) -> None:
        for stop in self.stops.values():
            stop.set()
        self.pool.shutdown(wait=False, cancel_futures=True)
        self.paths.close()
