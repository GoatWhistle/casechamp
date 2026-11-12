import json
from dataclasses import replace
from pathlib import Path
from typing import cast

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from app.adapter.traffic.calculation import TrafficCalculation
from app.adapter.traffic.jobs import TrafficJobs
from app.domain.errors import InvalidQuery
from app.repository.clickhouse.records import decode, encode
from app.usecase.traffic import TrafficJob, TrafficScope


def snapshot(path: Path) -> None:
    pq.write_table(
        pa.table(
            {
                "src": [10, 20, 20, 30],
                "dst": [20, 10, 30, 20],
                "free_hours": [0.1] * 4,
                "capacity": [1800.0] * 4,
                "km": [5.0] * 4,
                "way_id": [100, 100, 200, 200],
                "shared": [False] * 4,
                "access": [True] * 4,
            }
        ),
        path / "edges.parquet",
    )
    pq.write_table(
        pa.table({"node": [10, 20, 30], "lat": [44.0] * 3, "lon": [42.0, 42.05, 42.1]}),
        path / "nodes.parquet",
    )
    pq.write_table(
        pa.table(
            {
                "point_id": ["a", "b"],
                "settlement": ["A", "B"],
                "region": ["R"] * 2,
                "population": [240000.0] * 2,
                "node": [10, 30],
                "lat": [44.0] * 2,
                "lon": [42.0, 42.1],
            }
        ),
        path / "places.parquet",
    )
    pq.write_table(
        pa.table(
            {
                "id": ["h1", "h2"],
                "lat": [44.0] * 2,
                "lon": [42.0, 42.1],
                "residential_m2_proxy": [100.0] * 2,
            }
        ),
        path / "housing.parquet",
    )
    (path / "source.json").write_text(json.dumps({"sha256": {"edges": "fixture"}}))


def geography(path: Path) -> Path:
    target = path / "geography.json"
    grid = [[0] * 30 for _ in range(8)]
    target.write_text(json.dumps({
        "origin_lon": 41.95, "origin_lat": 43.98, "cell_degrees": 0.01,
        "elevation_m": grid, "blocked": grid, "water": grid,
        "sources": {k: "synthetic test fixture" for k in ["elevation", "water", "buildings", "protected"]},
    }))
    return target


def test_housing_assignment_compares_fixed_demand_and_preserves_map(tmp_path: Path) -> None:
    snapshot(tmp_path)
    job = TrafficJob("traffic-test", TrafficScope(), status="running", bounds=[41, 43, 43, 45])
    updates: list[TrafficJob] = []
    result = TrafficCalculation(geography=geography(tmp_path), workers=2).run(job, tmp_path, updates.append, lambda: None)
    assert result.status == "completed"
    assert result.baseline and result.baseline.converged
    assert result.alternatives
    assert all(item.kind in {"capacity", "connection", "package"} for item in result.alternatives)
    assert all(item.vehicle_hours_saved is not None for item in result.alternatives)
    assert json.loads(result.provenance)["housing"]["allocated_population"] == 480000
    assert result.roads and result.zones
    assert any(
        item.vehicle_hours_saved > 0
        for item in result.alternatives
        if item.vehicle_hours_saved is not None
    )
    restored = decode(TrafficJob, json.loads(json.dumps(encode(TrafficJob, result))))
    assert restored == result
    observations = json.loads(restored.provenance)["verified_observations"]
    assert len(observations) == json.loads(restored.provenance)["verified_projects"]
    assert all(row["metric"] == "local_accessibility_delta" for row in observations)
    assert all(row["assignment_converged"] for row in observations)
    assert any(row["gain"] <= 0 for row in observations)
    assert {item.stage for item in updates} >= {"baseline", "candidates", "comparing"}


def test_pair_has_declared_load_and_no_housing_background(tmp_path: Path) -> None:
    snapshot(tmp_path)
    scope = TrafficScope(places=["A", "B"], region="R", pair_flow=1000, demand_multiplier=1.3)
    result = TrafficCalculation(geography=geography(tmp_path), workers=2).run(
        TrafficJob("traffic-test", scope), tmp_path, lambda job: None, lambda: None
    )
    evidence = json.loads(result.provenance)
    assert evidence["generated_vehicles_per_hour"] == 1300
    assert evidence["od_pairs"] == 1
    assert result.baseline and result.baseline.unserved_vehicles == 0


def test_cancellation_stops_assignment_before_claiming_completion(tmp_path: Path) -> None:
    snapshot(tmp_path)

    def stop() -> None:
        raise InterruptedError()

    with pytest.raises(InterruptedError):
        TrafficCalculation(geography=geography(tmp_path), workers=2).run(
            TrafficJob("traffic-test", TrafficScope()), tmp_path, lambda job: None, stop
        )


def test_invalid_scope_fails_before_storage_or_network() -> None:
    with pytest.raises(InvalidQuery):
        TrafficJobs.submit(
            cast(TrafficJobs, None), replace(TrafficScope(), demand_multiplier=float("nan"))
        )


def test_single_proposal_checks_network_interventions_without_speed_overrides(
    tmp_path: Path,
) -> None:
    snapshot(tmp_path)
    job = TrafficJob(
        "traffic-test", TrafficScope(places=["A", "B"], pair_flow=1000, max_projects=1)
    )
    result = TrafficCalculation(geography=geography(tmp_path), workers=2).run(job, tmp_path, lambda _: None, lambda: None)
    assert len(result.alternatives) == 1
    assert result.alternatives[0].kind in {"capacity", "connection", "package"}
    assert json.loads(result.provenance)["evaluated_projects"] > 3
