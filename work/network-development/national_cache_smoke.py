import json
import os
import time
from pathlib import Path

import numpy as np
from app.adapter.road_graph.data import GraphData
from app.adapter.road_graph.weighted import minimum_csr
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.graph_snapshot import ClickHouseGraphSnapshot
from synthetic_traffic.index_paths import DiskGraphCache


def main():
    root=Path(__file__).resolve().parents[2]
    env={}
    for line in (root/'.env.analytics').read_text().splitlines():
        if '=' in line and not line.lstrip().startswith('#'):
            key,value=line.split('=',1)
            env[key.strip()]=value.strip().strip('\"').strip("'")
    reader=ClickHouseReader(env['CLICKHOUSE_URL'],env.get('CLICKHOUSE_USER','plexus'),env['CLICKHOUSE_PASSWORD'])
    data=GraphData(root/'data/graph_ru',ClickHouseGraphSnapshot(reader))
    start=time.monotonic()
    data.load()
    print(json.dumps({'stage':'loaded','seconds':time.monotonic()-start}),flush=True)
    e=data.edges
    keep=data.allowed_edges('road') & np.isfinite(e['h'])
    cities=data.read('cities')
    count=max(len(data.nodes['lat']),max(int(c[1])+1 for c in cities))
    graph=minimum_csr(e['src'][keep],e['dst'][keep],e['h'][keep],count)
    print(json.dumps({'stage':'csr','seconds':time.monotonic()-start,'nodes':count,'edges':graph.nnz}),flush=True)
    origin=int(cities[0][1])
    prep=time.monotonic()
    cache=DiskGraphCache(graph,[origin],root/'data/graph_ru/incremental-index-smoke')
    print(json.dumps({'stage':'tree','seconds':time.monotonic()-prep}),flush=True)
    changed=graph.copy()
    parents=np.asarray(cache.trees[origin].parent)
    targets=np.flatnonzero(parents>=0)
    target=int(targets[len(targets)//2])
    source=int(parents[target])
    left,right=changed.indptr[source:source+2]
    position=int(left+np.searchsorted(changed.indices[left:right],target))
    changed.data[position]*=1.2
    fork=cache.fork()
    tick=time.monotonic()
    try:
        fork.update_graph(changed,deadline=tick+60)
        status='verified'
    except TimeoutError:
        status='deadline'
    report={'status':status,'nodes':count,'edges':graph.nnz,'markets':1,
            'baseline_seconds':tick-prep,'delta_seconds':time.monotonic()-tick,
            'changed_nodes':fork.changed_nodes,'repaired_origins':fork.repaired_origins}
    fork.close()
    (root/'work/network-development/national-cache-smoke.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report),flush=True)


if __name__=='__main__':
    main()
