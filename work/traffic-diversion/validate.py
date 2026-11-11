import json
import os
from dataclasses import asdict
from pathlib import Path
from time import monotonic
from types import SimpleNamespace

from app.adapter.chat.artifacts import ChatRun
from app.adapter.chat.network_scenarios import NetworkScenarios
from app.adapter.chat.network_jobs import NetworkJobs
from app.adapter.chat.scenario_requests import ConnectivityScenario, ConnectivityEconomics
from app.adapter.road_corridor.resolver import CorridorResolver
from app.adapter.road_graph.jobs import RoadJobs
from app.domain.traffic_diversion import TrafficAssumptions
from app.domain.transport import NetworkMode, Season
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.graph_snapshot import ClickHouseGraphSnapshot
from app.repository.clickhouse.state import ClickHouseRoadJobStore
from app.settings import load_settings
from app.usecase.chat import ChatContext
from app.usecase.road_corridor import RoadCorridors

output = Path('work/traffic-diversion')
config = load_settings(os.environ)
reader = ClickHouseReader(config.clickhouse_url, config.clickhouse_user, config.clickhouse_password)
roads = RoadJobs(Path('data'), ClickHouseGraphSnapshot(reader), ClickHouseRoadJobStore(reader))
try:
    resolver = CorridorResolver(roads)
    corridors = RoadCorridors(resolver)
    places = ['Кочубеевское, Ставропольский край', 'Невинномысск, Ставропольский край']
    bridges = corridors.bridges(places[0], 20, 'Р-217')
    (output / 'bridges.json').write_text(json.dumps([asdict(b) for b in bridges], ensure_ascii=False, indent=2))
    print('bridges', [(b.corridor.id, b.distance_km, b.corridor.way_ids) for b in bridges], flush=True)
    if not bridges:
        raise RuntimeError('No matching bridge')
    closest = next(b for b in bridges if set(b.corridor.way_ids) == {37787244, 133175822})
    selected = [closest.corridor.id]
    (output / 'selection.json').write_text(json.dumps(asdict(closest), ensure_ascii=False, indent=2))
    run = ChatRun(ChatContext(None, Season.SUMMER, NetworkMode.ROAD, 'hansen'))
    start = monotonic()
    result = json.loads(NetworkScenarios(None, corridors, None).calculate_scenario(
        SimpleNamespace(deps=run), ConnectivityScenario('connectivity', places, selection_ids=selected,
                                                       traffic=TrafficAssumptions()),
    ))
    result['validation_elapsed_seconds'] = monotonic() - start
    (output / 'result.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
    (output / 'events.json').write_text(json.dumps([asdict(e) for e in run.pending], ensure_ascii=False, indent=2))
    restored = RoadCorridors(CorridorResolver(roads))
    economics = json.loads(NetworkJobs(None, None, restored).manage_calculation(
        SimpleNamespace(deps=ChatRun(run.context)), ConnectivityEconomics('connectivity_economics', result['calculation_id']),
    ))
    (output / 'economics.json').write_text(json.dumps(economics, ensure_ascii=False, indent=2))
    print(json.dumps(result, ensure_ascii=False), flush=True)
    print(json.dumps(economics, ensure_ascii=False), flush=True)
finally:
    roads.close()
