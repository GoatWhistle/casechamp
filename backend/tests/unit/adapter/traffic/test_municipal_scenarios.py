from pathlib import Path
from time import monotonic, sleep

import pytest
from synthetic_traffic.baseline_store import save_baseline
from synthetic_traffic.incremental import prepare_incremental
from synthetic_traffic.model import Trip
from synthetic_traffic.source import load_network
from tests.unit.adapter.traffic.snapshot_fixture import snapshot

from app.adapter.traffic.municipal_connectivity import MunicipalConnectivity
from app.adapter.traffic.municipal_scenarios import MunicipalScenarioJobs
from app.domain.errors import DataUnavailable, InvalidQuery
from app.usecase.municipal_scenarios import MunicipalScenarioRequest
from app.usecase.traffic import TrafficIndexChange, TrafficIndexValue, TrafficJob


class Store:
    def __init__(self) -> None:
        self.items: dict[str, TrafficJob] = {}

    def load(self) -> list[TrafficJob]:
        return list(self.items.values())

    def save(self, job: TrafficJob) -> None:
        self.items[job.id] = job


def test_requires_published_baseline_and_valid_identifier(tmp_path: Path) -> None:
    jobs = MunicipalScenarioJobs(tmp_path, Store())
    try:
        with pytest.raises(InvalidQuery):
            jobs.submit(MunicipalScenarioRequest('../escape', 'region', 'municipality', 'closure', [1]))
        with pytest.raises(DataUnavailable):
            jobs.submit(MunicipalScenarioRequest('absent', 'region', 'municipality', 'closure', [1]))
    finally:
        jobs.close()


def test_closed_route_keeps_lost_demand_and_does_not_claim_time_savings(tmp_path: Path) -> None:
    source = tmp_path / "source"
    source.mkdir()
    snapshot(source)
    base = prepare_incremental(load_network(source), [Trip(0, 2, 100)])
    save_baseline(base, tmp_path / "published")
    store = Store()
    jobs = MunicipalScenarioJobs(tmp_path, store)
    try:
        job = jobs.submit(MunicipalScenarioRequest("published", "R", "M", "closure", [100]))
        deadline = monotonic() + 10
        while jobs.get(job.id).status in {"queued", "running"} and monotonic() < deadline:
            sleep(0.01)
        result = jobs.get(job.id)
        assert result.status == "completed", result.error
        assert result.alternatives[0].after.unserved_vehicles == 100
        assert result.alternatives[0].vehicle_hours_saved is None
        assert result.alternatives[0].length_km == 5
        assert any(road.project and road.flow_before > 0 and road.flow_after == 0 for road in result.roads)
        assert store.items[result.id] == result
        assert result.assignment_progress is not None
        assert result.assignment_progress.iteration >= 1
        assert result.assignment_progress.relative_gap == result.alternatives[0].after.relative_gap
    finally:
        jobs.close()


@pytest.mark.parametrize("available", [True, False])
def test_scenario_completes_only_with_connectivity_effects(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, available: bool) -> None:
    source = tmp_path / "source"
    source.mkdir()
    snapshot(source)
    base = prepare_incremental(load_network(source), [Trip(0, 2, 100)])
    save_baseline(base, tmp_path / "published")

    def evaluate(*args: object) -> tuple[list[TrafficIndexValue], list[TrafficIndexChange]]:
        if not available:
            raise DataUnavailable("Connectivity baseline is missing")
        return ([TrafficIndexValue("R", 100, 100, 2, 175)],
                [TrafficIndexChange("R", 100, 80, -20, -20, 100)])

    monkeypatch.setattr(MunicipalConnectivity, "evaluate", evaluate)
    jobs = MunicipalScenarioJobs(tmp_path, Store(), connectivity=object.__new__(MunicipalConnectivity))
    try:
        job = jobs.submit(MunicipalScenarioRequest("published", "R", "M", "closure", [100]))
        deadline = monotonic() + 10
        while jobs.get(job.id).status in {"queued", "running"} and monotonic() < deadline:
            sleep(.01)
        result = jobs.get(job.id)
        if available:
            assert result.status == "completed"
            assert result.alternatives[0].indices[0].delta == -20
            assert result.indices[0].normalization == 175
            assert result.completed == result.total == 4
        else:
            assert result.status == "failed"
            assert result.alternatives == []
    finally:
        jobs.close()


def test_local_last_lane_closure_keeps_reverse_trips_and_saved_baseline(tmp_path: Path) -> None:
    source = tmp_path / 'source'
    source.mkdir()
    snapshot(source)
    base = prepare_incremental(load_network(source), [Trip(0, 2, 100), Trip(2, 0, 50)])
    save_baseline(base, tmp_path / 'published')
    checksum = (tmp_path / 'published' / 'sha256').read_bytes()
    jobs = MunicipalScenarioJobs(tmp_path, Store())
    try:
        job = jobs.submit(MunicipalScenarioRequest('published', 'R', 'M', 'lane_closure', [100], [0]))
        deadline = monotonic() + 10
        while jobs.get(job.id).status in {'queued', 'running'} and monotonic() < deadline:
            sleep(.01)
        result = jobs.get(job.id)
        assert result.status == 'completed', result.error
        assert result.alternatives[0].after.unserved_vehicles == 100
        assert result.alternatives[0].vehicle_hours_saved is None
        assert sum(road.closed is True for road in result.roads) == 1
        assert (tmp_path / 'published' / 'sha256').read_bytes() == checksum
        assert len(base.network.source) == 4
        assert base.assignment.unserved_vehicles_per_hour == 0
    finally:
        jobs.close()
