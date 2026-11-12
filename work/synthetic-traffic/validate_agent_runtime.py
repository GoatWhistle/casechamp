import json
import os
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

from app.adapter.road_graph.data import GraphData
from app.adapter.road_graph.routing import GraphRouting
from app.adapter.road_graph.shortest_paths import ShortestPaths
from app.adapter.traffic.calculation import TrafficCalculation
from app.adapter.traffic.indices import TrafficIndices
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.graph_snapshot import ClickHouseGraphSnapshot
from app.repository.clickhouse.traffic_state import ClickHouseTrafficStore
from app.settings import load_settings
from app.usecase.traffic import TrafficJob, TrafficScope


def main() -> None:
    config = load_settings(os.environ)
    reader = ClickHouseReader(config.clickhouse_url or "", config.clickhouse_user, config.clickhouse_password)
    data = GraphData(Path('/private/tmp/plexus-traffic-index-validation'), ClickHouseGraphSnapshot(reader))
    paths = ShortestPaths(4)
    indices = TrafficIndices(data, GraphRouting(data, paths))
    store = ClickHouseTrafficStore(reader)
    pointer = json.loads(Path('/private/tmp/plexus-traffic-index-job.json').read_text())
    source = Path('/private/tmp/plexus-traffic-runtime/traffic') / pointer['id']
    scope = TrafficScope(bounds=[41.55,43.8,42.25,44.95], max_projects=3)
    job = TrafficJob('traffic-' + uuid4().hex, scope, status='running', stage='baseline', bounds=scope.bounds)
    Path('/private/tmp/plexus-traffic-parallel-job.json').write_text(json.dumps(asdict(job)))
    stage = ''
    def update(value: TrafficJob) -> None:
        nonlocal stage
        store.save(value)
        if value.stage != stage or value.completed % 60 == 0:
            print(json.dumps({'id':value.id,'stage':value.stage,'completed':value.completed,'total':value.total}), flush=True)
            stage = value.stage
    try:
        result = TrafficCalculation(indices).run(job, source, update, lambda: None)
        store.save(result)
        report = asdict(result)
        report.pop('roads')
        report.pop('zones')
        for alternative in report['alternatives']:
            alternative['map_edges'] = len(alternative.pop('roads'))
        report['provenance'] = json.loads(result.provenance)
        report['verified_at'] = datetime.now(UTC).isoformat()
        Path('work/synthetic-traffic/agent-validation.json').write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False)+'\n')
        print(json.dumps({'id':result.id,'status':result.status,'indices':report['indices'],'alternatives':[(a['kind'],a['indices']) for a in report['alternatives']]}, ensure_ascii=False), flush=True)
    finally:
        paths.close()


if __name__ == '__main__':
    main()
