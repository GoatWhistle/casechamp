import time

import numpy as np
import pytest
from synthetic_traffic.alignment import prepare_alignment
from synthetic_traffic.alignment_validation import segment_details
from synthetic_traffic.candidates import generate_candidates
from synthetic_traffic.corridor import find_corridor
from synthetic_traffic.geography import RasterGeography, polyline_km
from synthetic_traffic.projects import apply_project
from test_traffic_candidate_targets import network


def surface():
    return RasterGeography(
        40,
        50,
        0.001,
        np.zeros((12, 12)),
        np.zeros((12, 12), bool),
        np.zeros((12, 12), bool),
        {
            key: "test fixture"
            for key in ("elevation", "water", "buildings", "protected")
        },
    )


def route(grid, cells):
    return {
        "geometry": {
            "type": "LineString",
            "coordinates": [grid.coordinate(cell) for cell in cells],
        },
        "structures": [],
    }


def test_staircase_artifacts_are_removed_without_global_speed_penalty():
    grid = surface()
    original = route(grid, [(2, 1), (2, 2), (3, 2), (3, 3), (4, 3), (4, 4), (5, 4)])
    result = prepare_alignment(original, grid)
    assert (
        result["geometry"]["coordinates"][0] == original["geometry"]["coordinates"][0]
    )
    assert (
        result["geometry"]["coordinates"][-1] == original["geometry"]["coordinates"][-1]
    )
    assert result["length_km"] < polyline_km(original["geometry"]["coordinates"])
    assert result["speed_kmh"] == pytest.approx(60)
    assert result["alignment_screening"]["simplified_vertices"] == 2
    assert result["alignment_screening"]["engineered_curve_radii_confirmed"] is False


def test_supercover_rejects_diagonal_corner_touch_and_unmarked_water():
    grid = surface()
    start, finish = grid.coordinate((2, 2)), grid.coordinate((3, 3))
    grid.blocked[2, 3] = True
    assert segment_details(grid, start, finish) is None
    grid.blocked[:] = False
    grid.water[2, 3] = True
    assert segment_details(grid, start, finish) is None


def test_shortcut_checks_intermediate_hill_not_only_endpoints():
    grid = surface()
    start, finish = grid.coordinate((4, 1)), grid.coordinate((4, 9))
    grid.elevation_m[4, 5] = 100
    assert grid.elevation_m[4, 1] == grid.elevation_m[4, 9] == 0
    assert segment_details(grid, start, finish) is None


def test_obstacle_detour_gets_validated_curves_and_local_travel_times():
    grid = surface()
    grid.blocked[3:8, 5] = True
    original = find_corridor(grid, grid.coordinate((5, 1)), grid.coordinate((5, 9)))
    assert original is not None
    result = prepare_alignment(original, grid)
    segments = result["travel_segments"]
    assert any(row["curve_radius_m"] is not None for row in segments)
    assert result["speed_kmh"] > min(row["speed_kmh"] for row in segments)
    assert result["free_travel_hours"] == pytest.approx(
        sum(row["free_hours"] for row in segments)
    )
    assert result["length_km"] / result["speed_kmh"] == pytest.approx(
        result["free_travel_hours"]
    )
    coordinates = result["geometry"]["coordinates"]
    for row in segments:
        assert (
            segment_details(grid, coordinates[row["from"]], coordinates[row["to"]])
            is not None
        )


def test_alignment_checks_generation_deadline_and_cancellation():
    grid = surface()
    original = route(grid, [(2, 1), (4, 4)])
    with pytest.raises(TimeoutError):
        prepare_alignment(original, grid, deadline=time.monotonic() - 1)

    def cancel():
        raise InterruptedError("cancelled")

    with pytest.raises(InterruptedError):
        prepare_alignment(original, grid, check=cancel)


def test_reported_minutes_match_applied_smoothed_segment_time(monkeypatch):
    graph = network()
    graph.lon += 40
    graph.lat += 50
    grid = surface()
    original_lengths = []

    def traced(surface, start, finish, deadline, penalty):
        coordinates = [
            start,
            [start[0], start[1] + 0.002],
            [finish[0], finish[1] + 0.002],
            finish,
        ]
        length = polyline_km(coordinates)
        original_lengths.append(length)
        return {
            "geometry": {"type": "LineString", "coordinates": coordinates},
            "length_km": length,
            "structures": [],
        }

    monkeypatch.setattr("synthetic_traffic.candidates.find_corridor", traced)
    result = generate_candidates(
        graph,
        np.ones(4),
        graph.free_hours,
        np.ones(4),
        limit=1,
        geography=grid,
        hypotheses=[
            {"source_node": 100, "target_node": 106, "origin": "agent_hypothesis"}
        ],
    )
    project = result["connections_for_review"][0]
    changed = apply_project(graph, project)
    assert project["length_km"] < original_lengths[0]
    assert changed.free_hours[-1] == pytest.approx(
        project["assumed_new_link_minutes"] / 60
    )
    assert changed.free_hours[-1] == pytest.approx(
        sum(row["free_hours"] for row in project["travel_segments"])
    )
