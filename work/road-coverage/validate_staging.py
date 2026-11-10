import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend/src'))
from app.adapter.road_graph.data import GraphData
from app.adapter.road_graph.delta_base import DeltaBase
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.graph_snapshot import ClickHouseGraphSnapshot

DEST = ROOT / 'data/road-refresh'


def mapped(sql):
    for name in ['graph', 'casechamp']:
        sql = sql.replace('plexus_' + name, 'plexus_refresh_' + name)
    for name in ['atlas_metadata', 'atlas_indices', 'atlas_exported_indices']:
        sql = sql.replace('plexus_atlas.' + name, 'plexus_refresh_atlas.' + name)
    return sql


class Reader(ClickHouseReader):
    def rows(self, sql, parameters):
        return super().rows(mapped(sql), parameters)

    def arrow(self, sql, parameters):
        return super().arrow(mapped(sql), parameters)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--wait', action='store_true')
    args = parser.parse_args()
    ready = DEST / 'staged-derived.json'
    while not ready.exists() or not json.loads(ready.read_text()).get('corridors'):
        if not args.wait:
            raise SystemExit('Derived tables not ready')
        time.sleep(30)
    reader = Reader(os.environ['CLICKHOUSE_URL'], os.environ['CLICKHOUSE_USER'], os.environ['CLICKHOUSE_PASSWORD'])
    data = GraphData(ROOT / 'data', ClickHouseGraphSnapshot(reader))
    assert data.modern_model
    version = reader.rows("SELECT value FROM plexus_atlas.atlas_metadata WHERE key='graph_version'", {})[0]['value']
    assert data.version == version
    checks = reader.rows("SELECT count() rows,uniqExact(region_id) regions,uniqExact(scenario) scenarios FROM plexus_atlas.atlas_indices", {})[0]
    assert checks == {'rows': 410, 'regions': 82, 'scenarios': 5}, checks
    graph = DeltaBase(data)
    regions = data.read('regions')
    assert len(regions) == 82
    results = []
    for (region,) in regions:
        baseline = graph.region(region)
        results.append(dict(region=region, expected=baseline.expected, actual=baseline.baseline_index,
                            difference=baseline.baseline_index - baseline.expected, points=len(baseline.ids)))
        print(f'{region}: {baseline.baseline_index:.8f} expected={baseline.expected:.8f}', flush=True)
        graph.regions.clear()
    report = dict(version=version, revision=data.revision, regions_checked=len(results), checks=results)
    (DEST / 'staging-validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print('All 82 regional runtime baselines match the staged index snapshot', flush=True)


if __name__ == '__main__':
    main()
