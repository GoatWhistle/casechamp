import json
from dataclasses import asdict
from unittest.mock import Mock

from app.domain.traffic_diversion import Detour, TrafficAssumptions, assign_diversion
from app.usecase.closure_assessment import closure_traffic
from app.usecase.road_stress import StressJob


def test_saved_traffic_keeps_overload_evidence_and_excludes_other_closures_and_versions() -> None:
    corridors = Mock()
    traffic = assign_diversion(3600, [Detour(1, 900)], TrafficAssumptions())
    saved = {
        "calculation_id": "traffic",
        "graph_version": "v",
        "traffic_assumptions": asdict(traffic.assumptions),
        "pairs": [
            {
                "origin": {"name": "Origin"},
                "destination": {"name": "Market"},
                "before": {"hours": 1},
                "after": {"hours": 2},
                "time_loss_pcu_hours": 1200,
                "traffic": asdict(traffic),
            }
        ],
    }
    corridors.recent_connectivity.return_value = json.dumps(
        [
            {"calculation_id": "traffic", "closed_way_ids": [10]},
            {"calculation_id": "old", "closed_way_ids": [10]},
            {"calculation_id": "joint", "closed_way_ids": [10, 11]},
        ]
    )
    corridors.read_connectivity.side_effect = lambda key: json.dumps(
        saved | ({"graph_version": "old"} if key == "old" else {})
    )
    evidence = closure_traffic(corridors, StressJob("stress", "v", [10]))
    assert len(evidence) == 1
    pairs = evidence[0]["pairs"]
    assert isinstance(pairs, list)
    pair = pairs[0]
    assert pair["detours"][0]["demand_capacity_ratio"] > 1
    assert pair["detours"][0]["capacity_pcu_h"] == 900
    assert pair["queue_at_end_pcu"] > 0
    assumptions = evidence[0]["assumptions"]
    assert isinstance(assumptions, dict)
    assert assumptions["utilization"] == 0.5
    assert corridors.read_connectivity.call_count == 2
