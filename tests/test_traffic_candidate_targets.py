import numpy as np
import pytest
from scipy.sparse.csgraph import connected_components
from synthetic_traffic import candidate_targets
from synthetic_traffic.assignment import route_graph
from synthetic_traffic.candidate_targets import rank_targets
from synthetic_traffic.candidates import generate_candidates
from synthetic_traffic.geography import RasterGeography, polyline_km
from synthetic_traffic.model import Network, Trip


def network():
    return Network(
        source=np.array([0, 1, 4, 5]),
        target=np.array([1, 2, 5, 6]),
        free_hours=np.array([0.5, 0.5, 0.0001, 0.0001]),
        capacity=np.full(4, 1800.0),
        length_km=np.full(4, 0.1),
        way_id=np.arange(4),
        raw_nodes=np.arange(100, 107),
        lat=np.full(7, 0.002),
        lon=np.arange(7) * 0.001 + 0.001,
        shared=np.full(4, -1),
    )


def targets(graph, trips, **options):
    routing, _ = route_graph(graph, graph.free_hours)
    _, components = connected_components(routing, directed=True, connection="strong")
    return rank_targets(
        graph, graph.free_hours, np.arange(7), components, trips=trips, **options
    )


def test_measured_detour_outranks_busy_pair_with_no_link_potential():
    rows = targets(network(), [Trip(4, 6, 10000), Trip(0, 2, 10)])
    assert [(row["source_index"], row["target_index"]) for row in rows] == [(0, 2)]
    assert rows[0]["potential_time_saving_minutes"] > 59
    assert rows[0]["target_reason"] == "fixed_od_detour"
    assert "not_verified_effect" in rows[0]["potential_basis"]


def test_disconnected_demand_is_not_sorted_after_connected_candidates():
    rows = targets(network(), [Trip(0, 2, 100), Trip(0, 4, 1)])
    assert rows[0]["disconnected"]
    assert rows[0]["target_index"] == 4
    assert rows[0]["current_between_endpoint_minutes"] is None


def test_each_origin_routes_once_and_reports_diagnostics(monkeypatch):
    calls = []
    original = candidate_targets.dijkstra

    def measured(*args, **kwargs):
        calls.append(kwargs["indices"])
        return original(*args, **kwargs)

    monkeypatch.setattr(candidate_targets, "dijkstra", measured)
    diagnostics = {}
    targets(network(), [Trip(0, 2, 10), Trip(0, 4, 2)], diagnostics=diagnostics)
    assert calls == [0]
    assert diagnostics["dijkstra_origins"] == 1
    assert diagnostics["eligible_targets"] == 2


@pytest.mark.parametrize(
    "hint",
    [
        {"source_node": 999, "target_node": 102},
        {"source_node": True, "target_node": 102},
        {"source_node": 100, "target_node": 100},
        {"source_node": 100, "target_node": 102, "priority": float("nan")},
    ],
)
def test_invalid_hypotheses_are_rejected(hint):
    with pytest.raises(ValueError):
        targets(network(), [], hypotheses=[hint])


def test_geographic_separation_skips_valid_hypothesis_with_diagnostic():
    diagnostics = {}
    result = targets(
        network(),
        [],
        hypotheses=[{"source_node": 100, "target_node": 102}],
        geography_groups={node: node for node in range(7)},
        diagnostics=diagnostics,
    )
    assert result == []
    assert (
        diagnostics["hypothesis_rejection_counts"][
            "snap_endpoints_in_separate_geographic_components"
        ]
        == 1
    )
    assert diagnostics["hypotheses_accepted_for_screening"] == 0


def test_only_grounded_index_priority_gets_priority_queue():
    rows = targets(
        network(),
        [Trip(0, 2, 10)],
        hypotheses=[
            {
                "source_node": 100,
                "target_node": 102,
                "origin": "index_route",
                "reason": "Market detour",
                "priority": 0.1,
            },
            {
                "source_node": 104,
                "target_node": 100,
                "origin": "index_route",
                "reason": "Market access gap",
                "priority": 0.2,
            },
            {"source_node": 102, "target_node": 104, "origin": "llm", "priority": 1e10},
        ],
    )
    indexed = [row for row in rows if row.get("target_origin") == "index_route"]
    assert [row["target_priority"] for row in indexed] == [0.2, 0.1]
    assert indexed[0]["target_rationale"] == "Market access gap"
    assert rows[0]["target_origin"] == "llm"


def test_first_route_pass_diversifies_endpoint_pairs(monkeypatch):
    graph = network()
    surface = RasterGeography(
        0,
        0,
        0.001,
        np.zeros((10, 10)),
        np.zeros((10, 10), bool),
        np.zeros((10, 10), bool),
        {
            key: "test fixture"
            for key in ("elevation", "water", "buildings", "protected")
        },
    )
    calls = []

    def route(surface, start, finish, deadline, penalty):
        calls.append((tuple(start), tuple(finish)))
        coordinates = [start, finish]
        return {
            "geometry": {"type": "LineString", "coordinates": coordinates},
            "length_km": polyline_km(coordinates),
            "structures": [],
        }

    monkeypatch.setattr("synthetic_traffic.candidates.find_corridor", route)
    result = generate_candidates(
        graph,
        np.ones(4),
        graph.free_hours,
        np.ones(4),
        limit=2,
        geography=surface,
        trips=[Trip(0, 2, 10), Trip(4, 0, 1)],
    )
    assert len(result["connections_for_review"]) == 2
    assert len(set(calls)) == 2
    assert all(
        row["alignment_variant"] == 1 for row in result["connections_for_review"]
    )
    assert result["target_diagnostics"]["eligible_targets"] == 2


def test_missing_source_access_id_cannot_be_mistaken_for_next_raw_node():
    graph = network()
    graph.access_raw_nodes = np.array([99])
    surface = RasterGeography(
        0,
        0,
        0.001,
        np.zeros((10, 10)),
        np.zeros((10, 10), bool),
        np.zeros((10, 10), bool),
        {
            key: "test fixture"
            for key in ("elevation", "water", "buildings", "protected")
        },
    )
    result = generate_candidates(
        graph,
        np.ones(4),
        graph.free_hours,
        np.ones(4),
        geography=surface,
        hypotheses=[{"source_node": 100, "target_node": 102}],
    )
    assert result["connections_for_review"] == []
    assert (
        result["target_diagnostics"]["hypothesis_rejection_counts"][
            "no_eligible_access_within_2km_existing_road"
        ]
        == 1
    )
