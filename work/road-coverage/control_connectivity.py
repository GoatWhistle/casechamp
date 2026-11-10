import gc
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'backend/src'))
from app.repository.clickhouse.client import ClickHouseReader

READER = ClickHouseReader(os.environ['CLICKHOUSE_URL'], os.environ['CLICKHOUSE_USER'], os.environ['CLICKHOUSE_PASSWORD'])


def connectivity(prefix):
    database = prefix + 'graph'
    n = READER.rows(f'SELECT count() n FROM {database}.nodes', {})[0]['n']
    way_table = READER.arrow(f'SELECT is_ferry,is_seasonal FROM {database}.ways ORDER BY way_idx', {})
    allowed = ~(way_table['is_ferry'].to_numpy() | way_table['is_seasonal'].to_numpy())
    edges = READER.arrow(f'SELECT src,dst,way_idx FROM {database}.edges', {})
    source, target, ways = [edges[name].to_numpy() for name in ['src','dst','way_idx']]
    keep = allowed[ways]
    matrix = coo_matrix((np.ones(int(keep.sum()), dtype=np.uint8), (source[keep], target[keep])), shape=(n,n)).tocsr()
    del edges, source, target, ways, keep, allowed, way_table
    _, component = connected_components(matrix, directed=False)
    del matrix
    cities = READER.rows(f'SELECT oktmo,node FROM {prefix}casechamp.market_cities', {})
    targets = np.array([c['node'] for c in cities if 0 <= c['node'] < n], dtype=np.int64)
    market_components = np.unique(component[targets])
    points = READER.arrow(f'SELECT point_id,region,population,node FROM {database}.points', {}).to_pandas()
    points = points[~points.region.isin(['Москва','Санкт-Петербург','Севастополь'])].copy()
    valid = (points.node >= 0) & (points.node < n)
    points['reachable'] = False
    points.loc[valid, 'reachable'] = np.isin(component[points.loc[valid,'node']], market_components)
    points.loc[points.point_id.isin([c['oktmo'] for c in cities]), 'reachable'] = True
    assert len(points) == 155412 and points.point_id.is_unique
    return points.drop(columns='node')


def main():
    before = connectivity('plexus_')
    gc.collect()
    after = connectivity('plexus_refresh_')
    rows = before.merge(after[['point_id','reachable']],on='point_id',suffixes=('_before','_after'),validate='one_to_one')
    rows['gained'] = ~rows.reachable_before & rows.reachable_after
    rows['lost'] = rows.reachable_before & ~rows.reachable_after
    rows['gained_population'] = rows.population.where(rows.gained,0)
    rows['lost_population'] = rows.population.where(rows.lost,0)
    regional = rows.groupby('region').agg(points=('point_id','size'), reachable_before=('reachable_before','sum'), reachable_after=('reachable_after','sum'), gained=('gained','sum'), lost=('lost','sum'), gained_population=('gained_population','sum'), lost_population=('lost_population','sum'))
    assert len(regional) == 82
    out = Path(__file__).resolve().parent
    regional.to_csv(out/'road-only-control-regions.csv')
    rows[rows.gained | rows.lost].to_csv(out/'road-only-control-changes.csv',index=False)
    report = dict(regions=82,points=len(rows),reachable_before=int(rows.reachable_before.sum()),reachable_after=int(rows.reachable_after.sum()),
        gained=int(rows.gained.sum()),lost=int(rows.lost.sum()),gained_population=int(rows.gained_population.sum()),lost_population=int(rows.lost_population.sum()),
        method='Both graphs exclude is_ferry and is_seasonal, use undirected components and their market anchors; own-market origins remain reachable. No trunk or manual links, no index comparison.')
    (out/'road-only-control.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2),flush=True)


if __name__ == '__main__':
    main()
