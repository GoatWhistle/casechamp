import pytest

from app.domain.errors import InvalidQuery
from app.domain.traffic_diversion import Detour, TrafficAssumptions, assign_diversion


def test_two_lane_flow_overloads_single_lane_detour_and_conserves_demand() -> None:
    result = assign_diversion(3600, [Detour(0.1, 1800)], TrafficAssumptions())
    assert result.displaced_flow_pcu_h == result.assigned_flow_pcu_h == 1800
    assert result.unserved_flow_pcu_h == 0
    assert result.routes[0].demand_capacity_ratio == 1.5
    assert result.queue_at_end_pcu == pytest.approx(900)
    assert result.routes[0].mean_queue_hours == pytest.approx(0.25)
    assert result.mean_detour_hours == pytest.approx(0.365)


def test_longer_closure_accumulates_queue_without_inventing_lost_capacity() -> None:
    result = assign_diversion(3600, [Detour(0.1, 1800)], TrafficAssumptions(duration_hours=2))
    assert result.queue_at_end_pcu == pytest.approx(1800)
    assert result.mean_detour_hours == pytest.approx(0.615)


def test_parallel_alternatives_split_the_same_flow_once() -> None:
    result = assign_diversion(3600, [Detour(0.1, 1800), Detour(0.1, 1800)], TrafficAssumptions())
    assert [r.flow_pcu_h for r in result.routes] == pytest.approx([900, 900])
    assert result.queue_at_end_pcu == pytest.approx(0, abs=1e-8)
    assert result.mean_detour_hours == pytest.approx(0.115)


def test_no_detour_retains_all_unserved_demand() -> None:
    result = assign_diversion(3600, [], TrafficAssumptions())
    assert result.unserved_flow_pcu_h == 1800
    assert result.assigned_flow_pcu_h == 0
    assert result.mean_detour_hours is None


@pytest.mark.parametrize(
    "assumptions",
    [
        TrafficAssumptions(utilization=1),
        TrafficAssumptions(duration_hours=0),
        TrafficAssumptions(duration_hours=float("nan")),
    ],
)
def test_invalid_assumptions_are_rejected(assumptions: TrafficAssumptions) -> None:
    with pytest.raises(InvalidQuery):
        assign_diversion(3600, [Detour(0.1, 1800)], assumptions)
