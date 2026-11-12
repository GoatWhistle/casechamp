import json
import time
from dataclasses import asdict
from pathlib import Path

from app.adapter.road_graph.data import GraphData
from app.adapter.traffic.calculation import TrafficCalculation
from app.adapter.traffic.indices import TrafficIndices
from app.adapter.traffic.index_delta import IndexDelta
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.graph_snapshot import ClickHouseGraphSnapshot
from app.usecase.traffic import TrafficJob, TrafficScope


def main():
    evaluate = IndexDelta.evaluate
    def measured(self, network, hours, deadline):
        started = time.monotonic()
        try:
            values = evaluate(self, network, hours, deadline)
            print(json.dumps({'index_seconds': time.monotonic()-started, 'delta': [v.value-b.value for v,b in zip(values,self.baseline)]}), flush=True)
            return values
        finally:
            print(json.dumps({'index_finished_seconds': time.monotonic()-started}), flush=True)
    IndexDelta.evaluate = measured
    root=Path(__file__).resolve().parents[2]
    env={}
    for line in (root/'.env.analytics').read_text().splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            key,value=line.split('=',1);env[key.strip()]=value.strip().strip('\"').strip("'")
    reader=ClickHouseReader(env['CLICKHOUSE_URL'],env.get('CLICKHOUSE_USER','plexus'),env['CLICKHOUSE_PASSWORD'])
    data=GraphData(root/'data/graph_ru',ClickHouseGraphSnapshot(reader))
    path=root/'data/traffic/traffic-8979fdc163fe491a95ca610ed2229033'
    source=json.loads((path/'source.json').read_text())
    job=TrafficJob('traffic-development-verification',TrafficScope(),bounds=source['bounds'])
    start=time.monotonic()
    last=[0.0]
    def checkpoint():
        if time.monotonic()-last[0]>30:
            print(json.dumps({'preparation_elapsed':round(time.monotonic()-start,2)}),flush=True)
            last[0]=time.monotonic()
    def update(value):
        print(json.dumps({'stage':value.stage,'elapsed':round(time.monotonic()-start,2)}),flush=True)
    result=TrafficCalculation(TrafficIndices(data),root/'data/traffic-geography/geography.json',32).run(job,path,update,checkpoint)
    out=root/'work/network-development/application-result.json'
    out.write_text(json.dumps(asdict(result),ensure_ascii=False))
    evidence=json.loads(result.provenance)
    print(json.dumps({'status':result.status,'alternatives':len(result.alternatives),
                      'search_seconds':evidence['search_seconds'],
                      'evaluated':evidence['evaluated_projects'],
                      'verified':evidence.get('verified_projects'),
                      'elapsed':time.monotonic()-start}),flush=True)


if __name__=='__main__':
    main()
