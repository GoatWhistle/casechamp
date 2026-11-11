import json
import os
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
from typing import cast

from app.adapter.road_corridor.connectivity import calculate_connectivity
from app.adapter.road_graph.data import GraphData
from app.adapter.road_graph.delta_base import DeltaBase
from app.adapter.road_graph.jobs import RoadJobs
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.graph_snapshot import ClickHouseGraphSnapshot
from app.settings import load_settings

config = load_settings(os.environ)
reader = ClickHouseReader(config.clickhouse_url, config.clickhouse_user, config.clickhouse_password)
root = Path(__file__).resolve().parents[2] / 'data'
data = GraphData(root, ClickHouseGraphSnapshot(reader))
roads = cast(RoadJobs, SimpleNamespace(data=data, delta=SimpleNamespace(base=DeltaBase(data))))
saved = json.loads((root / 'connectivity-results/connectivity-7d8777d0b53c49a2835b6734c847712d.json').read_text())
result = calculate_connectivity(roads, ['Санкт-Петербург, Санкт-Петербург', 'Москва, Москва'], 'all_pairs', None, saved['closed_way_ids'])
assert result.pairs[0].before.status == 'reachable', result
assert result.pairs[0].after.status != 'unbound', result
output = Path(__file__).with_name('pair-validation.json')
output.write_text(json.dumps(asdict(result), ensure_ascii=False, indent=2))
pair = result.pairs[0]
print(json.dumps({'before': asdict(pair.before), 'after': asdict(pair.after), 'score_before': pair.score_before, 'score_after': pair.score_after, 'closure_ways': len(saved['closed_way_ids'])}, ensure_ascii=False))
