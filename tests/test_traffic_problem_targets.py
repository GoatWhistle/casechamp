import time

import numpy as np
from synthetic_traffic.candidate_targets import rank_targets
from synthetic_traffic.hypothesis_targets import diversify_targets
from synthetic_traffic.model import Network, Trip
from synthetic_traffic.problem_targets import (
    disconnected_problem_targets,
    interleave_problem_targets,
    path_problem_targets,
)


def test_internal_detour_and_congested_access_keep_actual_path_nodes():
    parents = np.arange(12) - 1
    rows = path_problem_targets(0, 11, parents, set(range(12)), 42, {(5, 6): 9})
    assert any(
        row[2] == "existing_route_detour_section" and row[0] > 0 and row[1] < 11
        for row in rows
    )
    bypass = next(row for row in rows if row[2] == "congested_access_bypass")
    assert bypass[:4] == (4, 7, "congested_access_bypass", 42)
    assert all(0 <= row[0] < row[1] <= 11 for row in rows)
    assert len(rows) <= 10


def test_deadline_prevents_path_walk():
    assert (
        path_problem_targets(
            0,
            4,
            np.arange(5) - 1,
            set(range(5)),
            1,
            {},
            deadline=time.monotonic() - 1,
        )
        == []
    )


def test_disconnected_demand_uses_known_endpoint_vicinity_nodes():
    coordinates = np.array([[0.0, 0, 0], [4.0, 0, 0], [5.0, 0, 0], [9.0, 0, 0]])
    rows = disconnected_problem_targets(
        0, 3, {0, 1, 2, 3}, np.array([0, 0, 1, 1]), coordinates, 7
    )
    assert rows[0][:4] == (1, 2, "disconnected_demand_endpoint_vicinity_gap", 7)
    assert all(row[4]["problem_od_source_index"] == 0 for row in rows)


def test_rank_targets_adds_interior_sections_with_actual_demand():
    network = Network(
        source=np.arange(11),
        target=np.arange(1, 12),
        free_hours=np.full(11, 0.1),
        capacity=np.full(11, 100.0),
        length_km=np.ones(11),
        way_id=np.arange(11),
        raw_nodes=np.arange(12),
        lat=np.zeros(12),
        lon=np.arange(12) * 0.001,
        shared=np.full(11, -1),
    )
    diagnostics = {}
    rows = rank_targets(
        network,
        np.full(11, 0.3),
        np.arange(12),
        np.zeros(12, dtype=int),
        trips=[Trip(0, 11, 42)],
        flow=np.full(11, 100),
        diagnostics=diagnostics,
    )
    internal = [
        row for row in rows if row["source_index"] > 0 and row["target_index"] < 11
    ]
    assert internal
    assert all(row["potential_weight"] == 42 for row in internal)
    assert any(row["target_reason"] == "congested_access_bypass" for row in rows)
    assert diagnostics["problem_paths_screened"] == 1
    assert diagnostics["problem_section_pairs"] <= 10


def test_problem_exposure_preserves_llm_diversity_quota():
    rows = [{"target_origin": "index_route", "id": i} for i in range(20)]
    rows += [{"target_origin": "problem_route", "id": "problem"}]
    rows += [{"target_origin": "agent_hypothesis", "id": "llm"}]
    result = diversify_targets(interleave_problem_targets(rows), 8)
    assert {"problem", "llm"} <= {row["id"] for row in result}
