from unittest.mock import Mock

from app.domain.errors import DataUnavailable
from app.usecase.municipal_improvement import propose_lane
from app.usecase.municipal_scenarios import MunicipalTrafficBaseline, MunicipalTrafficCorridor
from app.usecase.traffic import TrafficJob, TrafficRoad, TrafficScope


def test_proposal_starts_only_one_lane_in_the_highest_loaded_supported_direction() -> None:
    scenarios = Mock()
    roads = [TrafficRoad(10, [[40., 44.], [41., 44.]], 100., 100., 1.5, 1.5,
                         edge_index=4, reverse_edge_index=9, shared_lane=False),
             TrafficRoad(10, [[41., 44.], [40., 44.]], 200., 200., 2., 2.,
                         edge_index=9, reverse_edge_index=4, shared_lane=False),
             TrafficRoad(20, [], 500., 500., 5., 5., edge_index=3, shared_lane=True)]
    scenarios.baseline.return_value = MunicipalTrafficBaseline('saved', 'district', [
        MunicipalTrafficCorridor(10, 2., 10., 1., 'Main'),
        MunicipalTrafficCorridor(20, 5., 20., 2., capacity_eligible=False),
    ], roads, .001, None, 'sha', TrafficJob('base', TrafficScope()))
    scenarios.submit.return_value = TrafficJob('scenario', TrafficScope())
    result, job = propose_lane(scenarios, 'region', 'district')
    request = scenarios.submit.call_args.args[0]
    assert request.kind == 'capacity'
    assert request.edge_indices == [9]
    assert request.way_ids == [10]
    scenarios.submit.assert_called_once()
    assert result['effect_status'] == 'pending'
    assert job is not None and job.id == 'scenario'
    assert roads[0].flow_before == 100.


def test_missing_baseline_does_not_submit_or_invent_effects() -> None:
    scenarios = Mock()
    scenarios.baseline.side_effect = DataUnavailable('Not ready')
    result, job = propose_lane(scenarios, 'region', 'district')
    assert result['status'] == 'awaiting_baseline'
    assert result['effect_status'] == 'not_calculated'
    assert job is None
    scenarios.submit.assert_not_called()


def test_preview_returns_directional_hypothesis_without_submitting_or_claiming_effect() -> None:
    scenarios = Mock()
    road = TrafficRoad(10, [[40., 44.], [41., 44.]], 100., 100., .2, .2,
                       edge_index=4, reverse_edge_index=9, shared_lane=False)
    scenarios.baseline.return_value = MunicipalTrafficBaseline('preview', 'district', [
        MunicipalTrafficCorridor(10, .2, 10., 1., 'Main'),
    ], [road], .8, None, 'sha', TrafficJob('base', TrafficScope(), stage='preliminary'))
    result, job = propose_lane(scenarios, 'region', 'district')
    assert result['status'] == 'awaiting_routing_baseline'
    assert result['effect_status'] == 'not_calculated'
    assert result['capacity_deficit_confirmed'] is False
    assert isinstance(result['proposal'], dict)
    assert result['proposal']['edge_index'] == 4
    assert job is None
    scenarios.submit.assert_not_called()
