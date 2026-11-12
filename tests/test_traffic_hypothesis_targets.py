import numpy as np
import pytest
from synthetic_traffic import hypothesis_targets
from synthetic_traffic.candidate_targets import rank_targets
from synthetic_traffic.hypothesis_targets import diversify_targets, prepare_hypotheses
from synthetic_traffic.model import Trip
from test_traffic_candidate_targets import network


def test_blocked_town_endpoint_snaps_along_road_not_across_nearby_gap():
    graph = network()
    graph.lon[4] = graph.lon[0] + 0.00001
    reason = {"source_place": {"id": "town-a", "name": "Town A"}, "purpose": "bypass"}
    proposals, diagnostics = prepare_hypotheses(
        graph,
        np.array([2, 4, 6]),
        [
            {
                "source_node": 100,
                "target_node": 106,
                "reason": reason,
                "origin": "agent_hypothesis",
            },
        ],
    )
    assert len(proposals) == 1
    source, target, _, _, metadata = proposals[0]
    assert (source, target) == (2, 6)
    assert metadata["original_source_node"] == 100
    assert metadata["original_target_node"] == 106
    assert metadata["source_snap_road_km"] == pytest.approx(0.2)
    assert metadata["target_snap_road_km"] == 0
    assert metadata["hypothesis_reason"] == reason
    assert diagnostics["hypotheses_snapped_to_road_access"] == 1


@pytest.mark.parametrize("length,accepted", [(2.0, True), (2.0001, False)])
def test_snap_has_a_hard_two_kilometer_road_distance_limit(length, accepted):
    graph = network()
    graph.length_km[0] = length
    proposals, diagnostics = prepare_hypotheses(
        graph,
        np.array([1, 4]),
        [
            {"source_node": 100, "target_node": 104},
        ],
    )
    assert bool(proposals) is accepted
    if not accepted:
        assert (
            diagnostics["hypothesis_rejection_counts"][
                "no_eligible_access_within_2km_existing_road"
            ]
            == 1
        )


def test_unsnappable_stored_node_does_not_abort_other_pairs():
    graph = network()
    proposals, diagnostics = prepare_hypotheses(
        graph,
        np.array([1, 4, 6]),
        [
            {"source_node": 103, "target_node": 106},
            {"source_node": 100, "target_node": 104},
        ],
    )
    assert len(proposals) == 1
    assert diagnostics["hypotheses_accepted_for_screening"] == 1
    assert diagnostics["hypotheses_requested"] == 2
    assert diagnostics["hypothesis_rejections"][0]["source_node"] == 103


def test_snap_destinations_respect_source_access_whitelist():
    graph = network()
    graph.access_raw_nodes = np.array([102, 106])
    proposals, _ = prepare_hypotheses(
        graph,
        np.array([2, 6]),
        [
            {"source_node": 100, "target_node": 106},
        ],
    )
    assert proposals[0][0] == 2
    with pytest.raises(ValueError, match="whitelist"):
        prepare_hypotheses(graph, np.array([1, 6]), [])


def test_repeated_stored_node_uses_one_snap_dijkstra(monkeypatch):
    graph = network()
    calls = []
    original = hypothesis_targets.dijkstra

    def measured(*args, **kwargs):
        calls.append(kwargs["indices"])
        return original(*args, **kwargs)

    monkeypatch.setattr(hypothesis_targets, "dijkstra", measured)
    proposals, diagnostics = prepare_hypotheses(
        graph,
        np.array([1, 4, 6]),
        [
            {"source_node": 100, "target_node": 104},
            {"source_node": 100, "target_node": 106},
        ],
    )
    assert len(proposals) == 2
    assert calls == [0]
    assert diagnostics["hypothesis_snap_dijkstra_origins"] == 1


def test_missing_trusted_index_endpoint_skips_with_reason_but_bogus_generic_raises():
    graph = network()
    proposals, diagnostics = prepare_hypotheses(
        graph,
        np.array([1, 4]),
        [
            {"source_node": 999, "target_node": 104, "origin": "index_route"},
        ],
    )
    assert proposals == []
    assert diagnostics["index_hints_outside_eligible_geography"] == 1
    with pytest.raises(ValueError, match="stored"):
        prepare_hypotheses(
            graph, np.array([1, 4]), [{"source_node": 999, "target_node": 104}]
        )


def test_diversity_reserves_quarter_slots_without_changing_potential_scores():
    ordinary = [{"id": index, "potential_score": 100 - index} for index in range(20)]
    hints = [
        {
            "id": 100 + index,
            "potential_score": 0.01,
            "target_origin": "agent_hypothesis",
        }
        for index in range(4)
    ]
    diagnostics = {}
    ranked = diversify_targets(ordinary + hints, 16, diagnostics)
    assert [
        index
        for index, row in enumerate(ranked)
        if row.get("target_origin") == "agent_hypothesis"
    ] == [0, 4, 8, 12]
    assert all(
        row["potential_score"] == 0.01
        for row in ranked
        if row.get("target_origin") == "agent_hypothesis"
    )
    assert diagnostics["hypothesis_diversity_quota"] == 4


def test_duplicate_automatic_pair_retains_hypothesis_provenance():
    graph = network()
    diagnostics = {}
    rows = rank_targets(
        graph,
        graph.free_hours,
        np.arange(7),
        np.arange(7),
        trips=[Trip(0, 4, 100)],
        hypotheses=[
            {
                "source_node": 100,
                "target_node": 104,
                "origin": "agent_hypothesis",
                "reason": {"source_place": "Town A"},
            }
        ],
        diagnostics=diagnostics,
    )
    assert len(rows) == 1
    assert rows[0]["potential_score"] == 100
    assert {"agent_hypothesis", "fixed_od_detour"} <= {
        source["target_origin"] for source in rows[0]["source_provenance"]
    }
    assert rows[0]["hypothesis_reason"] == {"source_place": "Town A"}
