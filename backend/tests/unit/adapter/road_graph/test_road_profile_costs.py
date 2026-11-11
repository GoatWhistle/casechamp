from pathlib import Path
from typing import Any, Literal

import numpy as np
import pytest
from tests.unit.adapter.road_graph.test_routing import Snapshot

from app.adapter.road_graph.appraisal import AppraisalRouting
from app.adapter.road_graph.data import GraphData
from app.adapter.road_graph.freight_routes import freight_routes
from app.adapter.road_graph.road_profiles import profile_changes
from app.adapter.road_graph.search_cache import changed_weights
from app.domain.appraisal_inputs import DemandScenario, FreightFlow, ProjectAssumptions
from app.domain.errors import InvalidQuery
from app.usecase.road_profile_validation import validate_changes
from app.usecase.road_records import RoadChange


def profile(verified: bool = False) -> dict[str, Any]:
    return {
        "highway": "primary",
        "surface": "asphalt",
        "lanes_total": 2,
        "lanes_forward": 1,
        "lanes_backward": 1,
        "oneway": "no",
        "hourly_flow_pcu": 1800 if verified else None,
        "flow_verified": verified,
        "flow_source": "Counter" if verified else "",
        "flow_period": "2026 peak hour" if verified else "",
        "lane_data_usable": True,
    }


def test_widening_without_observation_has_no_time_bonus() -> None:
    changes, notes = profile_changes([RoadChange(101, lanes_total=4)], {101: 0}, {0: profile()})
    assert changes[0].speed_factor == 1
    assert "lanes_without_verified_flow_no_time_effect" in notes


def test_widening_holds_confirmed_absolute_flow_and_reduces_delay() -> None:
    base = profile(True)
    changes, notes = profile_changes([RoadChange(101, lanes_total=4)], {101: 0}, {0: base})
    assert changes[0].speed_factor > 1
    assert base["hourly_flow_pcu"] == 1800
    assert not notes


def test_surface_and_class_recompute_free_flow_with_no_traffic() -> None:
    base = {**profile(), "highway": "track", "surface": "ground"}
    changes, _ = profile_changes(
        [RoadChange(101, highway="motorway", surface="asphalt")], {101: 0}, {0: base}
    )
    assert changes[0].speed_factor == pytest.approx(90 / 14)


def test_manual_design_speed_is_not_capped_by_old_class_prior() -> None:
    changes, _ = profile_changes([RoadChange(101, speed_kmh=100)], {101: 0}, {0: profile()})
    assert changes[0].speed_factor == pytest.approx(100 / 60)


def test_profile_and_manual_factor_cannot_double_count() -> None:
    with pytest.raises(InvalidQuery):
        validate_changes([RoadChange(101, 1.2, lanes_total=4)])
    for change in [RoadChange(101, lanes_total=0), RoadChange(101, speed_kmh=float("nan"))]:
        with pytest.raises(InvalidQuery):
            validate_changes([change])


def test_legacy_manual_factor_stays_unchanged() -> None:
    edges = {"h": np.array([2.0]), "way_idx": np.array([0])}
    weights, changed = changed_weights(edges, {101: 0}, [RoadChange(101, 2)])
    assert weights[0] == 1
    assert changed == 1


def test_routed_freight_uses_road_only_time_and_km_of_same_fastest_path(tmp_path: Path) -> None:
    class MileageSnapshot(Snapshot):
        def arrays(self, name: Literal["edges", "nodes", "ranks", "seasons"]) -> dict[str, Any]:
            rows = super().arrays(name)
            if name == "edges":
                rows["km"][2] = 1
            return rows

    data = GraphData(tmp_path, MileageSnapshot())
    flow = FreightFlow(
        "Freight",
        100,
        None,
        None,
        None,
        None,
        500,
        10,
        "Assumed yearly demand",
        origin_point_id="origin",
        market_city="market",
    )
    before = freight_routes(data, "region", "road", [], [flow])
    after = freight_routes(data, "region", "road", [RoadChange(101, 0)], [flow])
    assert before["Freight"] == pytest.approx((2, 20))
    assert after["Freight"] == pytest.approx((5, 50))
    project = ProjectAssumptions(
        [],
        [DemandScenario("low", 0.5, 1), DemandScenario("base", 1, 1), DemandScenario("high", 2, 1)],
        0,
        0,
        1,
        0,
        2026,
        "No cost",
        [flow],
    )
    appraisal = AppraisalRouting(project)
    appraisal.freight_before, appraisal.freight_after = before, after
    result = appraisal.result()
    assert result.method == "conditional_flow_appraisal_v2"
    assert result.scenarios[1].annual_freight_rub == -180000
    assert result.freight_routing_scope == "road_network_vehicle_constraints_unverified"


def test_routed_freight_unavailable_evidence_does_not_use_manual_placeholder_values() -> None:
    flow = FreightFlow(
        "Freight",
        100,
        99,
        0,
        99,
        0,
        500,
        10,
        "Assumption",
        origin_point_id="origin",
        market_city="market",
    )
    project = ProjectAssumptions(
        [],
        [DemandScenario("low", 0.5, 1), DemandScenario("base", 1, 1), DemandScenario("high", 2, 1)],
        0,
        0,
        1,
        0,
        2026,
        "No cost",
        [flow],
    )
    result = AppraisalRouting(project).result()
    assert result.status == "incomplete"
    assert result.unresolved_freight_flows == 1
    assert result.scenarios[1].annual_freight_rub is None
    assert result.scenarios[1].net_present_value_rub is None


def test_routed_unused_manual_evidence_cannot_contain_nan() -> None:
    flow = FreightFlow(
        "Freight",
        100,
        float("nan"),
        None,
        None,
        None,
        500,
        10,
        "Assumption",
        origin_point_id="origin",
        market_city="market",
    )
    project = ProjectAssumptions(
        [],
        [DemandScenario("low", 0.5, 1), DemandScenario("base", 1, 1), DemandScenario("high", 2, 1)],
        0,
        0,
        1,
        0,
        2026,
        "No cost",
        [flow],
    )
    with pytest.raises(InvalidQuery):
        AppraisalRouting(project).result()
