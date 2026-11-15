import json
from types import SimpleNamespace

import numpy as np
import pytest
import synthetic_traffic.geography_queue_worker as worker
from synthetic_traffic.geography_queue_plan import plan, tiles_for
from synthetic_traffic.geography_queue_store import connect, exclusive, status
from synthetic_traffic.geography_queue_worker import run_queue


def boundary(identifier, bounds, polygons=None):
    west, south, east, north = bounds
    return {
        "id": identifier,
        "name": identifier,
        "bounds": bounds,
        "polygons": polygons
        or [
            [
                [
                    [west, south],
                    [east, south],
                    [east, north],
                    [west, north],
                    [west, south],
                ]
            ]
        ],
    }


def fetch(bounds, destination, cache, resolution=0.001, vector_cache=None):
    np.savez(destination / "geography.npz", elevation=np.zeros((2, 2)))
    return {
        "status": "complete",
        "source": "unit-test",
        "bounds": bounds,
        "resolution": resolution,
    }


def test_tiles_intersect_polygon_area_and_respect_holes():
    triangle = boundary("one", [0, 0, 1, 1], [[[[0, 0], [1, 0], [0, 1], [0, 0]]]])
    assert tiles_for(triangle) == {(360, 180), (361, 180), (360, 181)}
    shell = [[0, 0], [1.5, 0], [1.5, 1.5], [0, 1.5], [0, 0]]
    hole = [[0.5, 0.5], [1, 0.5], [1, 1], [0.5, 1], [0.5, 0.5]]
    tiles = tiles_for(boundary("hole", [0, 0, 1.5, 1.5], [[shell, hole]]))
    assert len(tiles) == 8 and (361, 181) not in tiles


def test_dateline_planning_does_not_cover_the_rest_of_the_world():
    row = boundary(
        "dateline",
        [179.5, 0, 180.5, 1],
        [[[[179.5, 0], [-179.5, 0], [-179.5, 1], [179.5, 1], [179.5, 0]]]],
    )
    assert tiles_for(row) == {(719, 180), (719, 181), (0, 180), (0, 181)}


def test_plan_prioritizes_stavropol_deduplicates_and_preserves_completed_tiles(
    tmp_path,
):
    rows = [
        boundary("001", [1, 1, 1.5, 1.5]),
        boundary("07000000", [1, 1, 1.5, 1.5]),
        boundary("002", [2, 2, 2.5, 2.5]),
    ]
    result = plan(rows, tmp_path)
    assert result["regions"] == 3 and result["tiles"] == {"pending": 2}
    assert result["coverage"]["region_ids"][0] == "07000000"
    with connect(tmp_path) as db:
        first = db.execute("SELECT * FROM tiles ORDER BY priority,id").fetchone()
        assert json.loads(first["region_ids"]) == ["07000000", "001"]
        db.execute("UPDATE tiles SET status='complete' WHERE id=?", (first["id"],))
    assert plan(rows, tmp_path)["tiles"] == {"complete": 1, "pending": 1}


def test_worker_limits_local_vector_cache_to_stavropol_and_resumes_interrupted(
    tmp_path,
):
    plan(
        [boundary("001", [2, 2, 2.5, 2.5]), boundary("07000000", [1, 1, 1.5, 1.5])],
        tmp_path,
    )
    with connect(tmp_path) as db:
        db.execute("UPDATE tiles SET status='running',attempts=1 WHERE priority=0")
    vector_file = tmp_path / "source.sqlite"
    vector_file.touch()
    caches = []

    def collect(*args, **kwargs):
        caches.append(kwargs["vector_cache"])
        return fetch(*args, **kwargs)

    result = run_queue(
        tmp_path,
        collect,
        vector_cache=vector_file,
        pause=lambda _: None,
        delay=0,
        min_free=0,
    )
    assert result["state"] == "completed" and result["tiles"] == {"complete": 2}
    assert caches == [vector_file, None]
    with connect(tmp_path) as db:
        assert (
            db.execute("SELECT attempts FROM tiles WHERE priority=0").fetchone()[0] == 1
        )


def test_failures_retry_three_times_backoff_then_continue(tmp_path):
    plan(
        [boundary("07000000", [1, 1, 1.5, 1.5]), boundary("other", [2, 2, 2.5, 2.5])],
        tmp_path,
    )
    calls, waits = [], []

    def sometimes(bounds, *args, **kwargs):
        calls.append(bounds)
        if bounds[0] == 1:
            raise OSError("Temporary network failure")
        return fetch(bounds, *args, **kwargs)

    result = run_queue(tmp_path, sometimes, pause=waits.append, min_free=0)
    assert result["state"] == "completed_with_failures"
    assert result["tiles"] == {"complete": 1, "failed": 1}
    assert len(calls) == 4 and sum(waits) == 43
    with connect(tmp_path) as db:
        failed = db.execute(
            "SELECT attempts,last_error FROM tiles WHERE status='failed'"
        ).fetchone()
        assert failed[0] == 3 and "Temporary network failure" in failed[1]


def test_stop_disk_guards_and_exclusive_lock(tmp_path, monkeypatch):
    plan([boundary("07000000", [1, 1, 1.5, 1.5])], tmp_path)
    (tmp_path / "STOP").touch()
    assert run_queue(tmp_path, fetch, min_free=0)["state"] == "stopped"
    (tmp_path / "STOP").unlink()
    monkeypatch.setattr(worker, "disk_usage", lambda _: SimpleNamespace(free=1))
    assert run_queue(tmp_path, fetch, min_free=2)["state"] == "diskpaused"
    assert run_queue(tmp_path, fetch, min_free=0, max_data=1)["state"] == "diskpaused"
    with exclusive(tmp_path), pytest.raises(RuntimeError, match="locked"):
        run_queue(tmp_path, fetch, min_free=0)
    assert status(tmp_path)["tiles"] == {"pending": 1}


def test_missing_artifact_is_not_complete_and_status_before_plan_is_honest(tmp_path):
    assert status(tmp_path)["state"] == "unplanned"
    plan([boundary("07000000", [1, 1, 1.5, 1.5])], tmp_path)
    result = run_queue(
        tmp_path,
        lambda *args, **kwargs: {"source": "incomplete"},
        pause=lambda _: None,
        delay=0,
        min_free=0,
    )
    assert result["tiles"] == {"failed": 1}


def test_optional_pilot_bounds_prioritize_only_overlapping_stavropol_tiles(tmp_path):
    rows = [boundary("07000000", [1, 1, 2, 1.5]), boundary("other", [3, 1, 3.5, 1.5])]
    pilot = [1.6, 1.1, 1.9, 1.4]
    result = plan(rows, tmp_path, priority_bbox=pilot)
    assert result["coverage"]["priority_bbox"] == pilot
    with connect(tmp_path) as db:
        ordered = list(
            db.execute("SELECT bbox,priority FROM tiles ORDER BY priority,id")
        )
    assert [json.loads(row[0])[0] for row in ordered] == [1.5, 1, 3]
    assert [row[1] for row in ordered] == [0, 1, 2]
    plan(rows, tmp_path, priority_bbox=[3.1, 1.1, 3.4, 1.4])
    with connect(tmp_path) as db:
        ordered = list(
            db.execute("SELECT bbox,priority FROM tiles ORDER BY priority,id")
        )
    assert [json.loads(row[0])[0] for row in ordered] == [1, 1.5, 3]
    assert [row[1] for row in ordered] == [1, 1, 2]


def test_priority_bounds_must_be_valid_geographic_rectangle(tmp_path):
    rows = [boundary("07000000", [1, 1, 1.5, 1.5])]
    for invalid in ([1, 2, 3], [1, 1, 0, 2], [1, float("nan"), 2, 3]):
        with pytest.raises(ValueError, match="Priority bounds"):
            plan(rows, tmp_path, priority_bbox=invalid)
