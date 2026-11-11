import json
import os
from dataclasses import asdict
from pathlib import Path
from time import monotonic
from types import SimpleNamespace

import numpy as np
from scipy.sparse.csgraph import dijkstra
from app.adapter.road_graph.routing import minimum_csr

from app.adapter.chat.artifacts import ChatRun
from app.adapter.chat.network_scenarios import NetworkScenarios
from app.adapter.chat.scenario_requests import ConnectivityScenario
from app.adapter.road_corridor.resolver import CorridorResolver
from app.adapter.road_graph.jobs import RoadJobs
from app.domain.transport import NetworkMode, Season
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.graph_snapshot import ClickHouseGraphSnapshot
from app.repository.clickhouse.state import ClickHouseRoadJobStore
from app.settings import load_settings
from app.usecase.chat import ChatContext
from app.usecase.road_corridor import RoadCorridors

output = Path('work/settlement-connectivity')
config = load_settings(os.environ)
reader = ClickHouseReader(config.clickhouse_url, config.clickhouse_user, config.clickhouse_password)
roads = RoadJobs(Path('data'), ClickHouseGraphSnapshot(reader), ClickHouseRoadJobStore(reader))
try:
    resolver = CorridorResolver(roads)
    corridors = RoadCorridors(resolver)
    places = [name + ', Ставропольский край' for name in (
        'Ставрополь', 'Александровское', 'Светлоград', 'Благодарный',
    )]
    start = monotonic()
    baseline = corridors.connectivity(places)
    assert len(baseline.pairs) == 6 and baseline.reachable_before == 6
    print('baseline', baseline.score_before, 'seconds', monotonic() - start, flush=True)
    points = roads.data.read('route_points', {'points': [p.id for p in baseline.places]})
    nodes = {str(p): (int(n), float(snap)) for p, n, snap in points}
    expected_times = dijkstra(roads.delta.base.graph, directed=True, indices=nodes[baseline.places[0].id][0])
    for pair in baseline.pairs:
        if pair.origin.id == baseline.places[0].id:
            expected = float(expected_times[nodes[pair.destination.id][0]])
            expected += (nodes[pair.origin.id][1] + nodes[pair.destination.id][1]) / 15
            assert abs(expected - pair.before.hours) < 1e-7
    route = resolver.resolve_route(places[0], places[1])
    print('resolved closure', len(route.corridor.way_ids), 'ways', flush=True)
    run = ChatRun(ChatContext(None, Season.SUMMER, NetworkMode.ROAD, 'hansen'))
    start = monotonic()
    result = json.loads(NetworkScenarios(None, corridors, None).calculate_scenario(
        SimpleNamespace(deps=run), ConnectivityScenario('connectivity', places, selection_ids=[route.corridor.id]),
    ))
    assert result['score_after'] <= result['score_before']
    assert len(result['pairs']) == 6
    for pair in result['pairs']:
        assert pair['score_after'] <= pair['score_before'] + 1e-8
    result['elapsed_seconds'] = monotonic() - start
    closed_indices = list(roads.data.indices_for(route.corridor.way_ids).values())
    keep = roads.data.allowed_edges('road') & ~np.isin(roads.data.edges['way_idx'], closed_indices)
    edges = roads.data.edges
    reference = minimum_csr(edges['src'][keep], edges['dst'][keep], edges['h'][keep], roads.delta.base.graph.shape[0])
    checked = 0
    for place in baseline.places[:-1]:
        times = dijkstra(reference, directed=True, indices=nodes[place.id][0])
        for pair in result['pairs']:
            if pair['origin']['id'] != place.id:
                continue
            expected = float(times[nodes[pair['destination']['id']][0]])
            if np.isfinite(expected):
                expected += (nodes[place.id][1] + nodes[pair['destination']['id']][1]) / 15
                assert abs(expected - pair['after']['hours']) < 1e-7
            else:
                assert pair['after']['status'] == 'unreachable'
            checked += 1
    assert checked == 6
    result['validation'] = {'independent_scipy_baseline_pairs': 3, 'independent_scipy_closure_pairs': 6, 'date': '2026-11-11', 'paid_llm': False}
    (output / 'baseline.json').write_text(json.dumps(asdict(baseline), ensure_ascii=False, indent=2))
    (output / 'closure.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
    (output / 'events.json').write_text(json.dumps([asdict(e) for e in run.pending], ensure_ascii=False, indent=2))
    print(json.dumps({k:result[k] for k in ('score_before','score_after','delta','disconnected_pairs','elapsed_seconds','graph_version')}, ensure_ascii=False), flush=True)
finally:
    roads.close()
