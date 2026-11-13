from pathlib import Path
from time import monotonic, sleep
from unittest.mock import Mock

from synthetic_traffic.baseline_store import load_baseline, save_baseline
from synthetic_traffic.incremental import prepare_incremental
from synthetic_traffic.model import Trip
from synthetic_traffic.source import load_network
from tests.unit.adapter.traffic.snapshot_fixture import snapshot
from tests.unit.adapter.traffic.test_municipal_scenarios import Store

from app.adapter.traffic.municipal_scenarios import MunicipalScenarioJobs
from app.adapter.traffic.municipal_social import MunicipalSocialAccess
from app.domain.normative.model import AccessRow, Facility
from app.usecase.municipal_scenarios import MunicipalScenarioRequest
from app.usecase.municipal_social import MunicipalSocialSource
from app.usecase.municipalities import Municipality


def test_closure_social_effects_use_same_scenario_and_survive_reload(tmp_path: Path) -> None:
    source = tmp_path / 'source'
    source.mkdir()
    snapshot(source)
    baseline = prepare_incremental(load_network(source), [Trip(0, 2, 100)])
    metadata = {'source': {'bounds': None, 'metadata': [{'key': 'graph_revision', 'value': 'graph'}]}}
    save_baseline(baseline, tmp_path / 'published', metadata)
    assert load_baseline(tmp_path / 'published').metadata == metadata
    rows = [AccessRow('village', 'Village', None, 44., 42., None, None, None, 'unknown',
                      routing_node=10, approach_metres=0.)]
    facilities = [Facility('hospital', 'medical', 'Hospital', '', '', '', 44., 42.1, None, 'known')]
    sources = Mock()
    sources.load.side_effect = lambda region, municipality, criterion: MunicipalSocialSource(
        criterion, 'sha', 'graph', rows, facilities,
    )
    store = Store()
    baselines = Mock()
    baselines.load.return_value = load_baseline(tmp_path / "published")
    baselines.get.return_value.baseline_id = 'published'
    baselines.get.return_value.corridors = [Mock(way_id=100)]
    baselines.selected_edges.return_value = [0, 1]
    baselines.municipality.return_value = Municipality(
        'M', 'R', 'District', 6, [[[(41., 43.), (43., 43.), (43., 45.), (41., 45.), (41., 43.)]]],
        '', '', '', '', 1.,
    )
    jobs = MunicipalScenarioJobs(tmp_path, store, baselines=baselines, social=MunicipalSocialAccess(sources))
    try:
        job = jobs.submit(MunicipalScenarioRequest('published', 'R', 'M', 'closure', [100]))
        deadline = monotonic() + 10
        while jobs.get(job.id).status in {'queued', 'running'} and monotonic() < deadline:
            sleep(.01)
        assert jobs.get(job.id).status == 'completed', jobs.get(job.id).error
        effects = jobs.effects(job.id)
        assert len(effects.social) == 6
        for effect in effects.social:
            assert effect.status == 'available'
            assert effect.lost_routes == 1
            assert effect.points[0].before_minutes is not None
            assert effect.points[0].after_minutes is None
        restored = MunicipalScenarioJobs(tmp_path, store)
        try:
            assert restored.effects(job.id) == effects
        finally:
            restored.close()
    finally:
        jobs.close()


def test_clipped_baseline_does_not_claim_cross_border_social_coverage() -> None:
    sources = Mock()
    baseline = Mock(metadata={'source': {'bounds': [41, 43, 43, 45]}})
    results = MunicipalSocialAccess(sources).evaluate(
        MunicipalScenarioRequest('published', 'R', 'M', 'closure', [100]),
        baseline, Mock(), [], lambda: None,
    )
    assert len(results) == 6
    assert all(row.status == 'unavailable' and row.reason == 'social_network_clipped_or_unknown'
               for row in results)
    sources.load.assert_not_called()
