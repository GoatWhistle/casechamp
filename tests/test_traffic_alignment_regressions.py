from itertools import pairwise

import pytest
from synthetic_traffic.alignment import prepare_alignment
from synthetic_traffic.alignment_validation import segment_details, structure_cells
from synthetic_traffic.corridor import find_corridor
from test_traffic_alignment import surface


def test_diagonal_grade_follows_bilinear_alignment_not_lateral_cell_edge():
    grid = surface()
    grid.elevation_m[2, 2] = 394.01605224609375
    grid.elevation_m[2, 3] = 400.1064147949219
    grid.elevation_m[3, 2] = 403.6064758300781
    grid.elevation_m[3, 3] = 409.208251953125
    detail = segment_details(grid, grid.coordinate((2, 3)), grid.coordinate((3, 2)))
    assert detail is not None
    assert detail["maximum_terrain_grade"] < 0.04
    assert detail["structure"] is None


def test_astar_routes_around_dry_diagonal_water_corner_without_fake_bridge():
    grid = surface()
    grid.water[3, 4] = True
    original = find_corridor(grid, grid.coordinate((3, 3)), grid.coordinate((4, 4)))
    assert original is not None
    assert original["structures"] == []
    for start, finish in pairwise(original["geometry"]["coordinates"]):
        assert segment_details(grid, start, finish) is not None
    assert prepare_alignment(original, grid)["length_km"] > 0


def test_real_water_crossing_retains_complete_bridge_footprint():
    grid = surface()
    grid.water[:, 5] = True
    original = find_corridor(grid, grid.coordinate((4, 2)), grid.coordinate((4, 8)))
    assert original is not None
    structures = structure_cells(grid, original)
    assert structures
    for start, finish in pairwise(original["geometry"]["coordinates"]):
        assert segment_details(grid, start, finish, structures) is not None
    smoothed = prepare_alignment(original, grid)
    assert any(row["structure"] == "bridge" for row in smoothed["travel_segments"])
    assert smoothed["speed_kmh"] < 60


def test_steep_crossing_retains_explicit_tunnel_anchors():
    grid = surface()
    grid.elevation_m[:, 5] = 100
    original = find_corridor(grid, grid.coordinate((4, 4)), grid.coordinate((4, 6)))
    assert original is not None
    assert any(item["kind"] == "tunnel" for item in original["structures"])
    smoothed = prepare_alignment(original, grid)
    assert any(row["structure"] == "tunnel" for row in smoothed["travel_segments"])
    assert smoothed["length_km"] / smoothed["speed_kmh"] == pytest.approx(
        smoothed["free_travel_hours"]
    )
