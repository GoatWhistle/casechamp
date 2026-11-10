import json
import os
from pathlib import Path
from time import monotonic

import duckdb
import numpy as np
import pyarrow.parquet as pq

from app.adapter.road_graph.data import GraphData
from app.adapter.road_graph.delta_base import DeltaBase
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.graph_snapshot import ClickHouseGraphSnapshot
from app.repository.clickhouse.airports import ClickHouseAirportRepository
from app.repository.clickhouse.atlas import ClickHouseAtlasRepository
from app.repository.files.airports import FileAirportRepository
from app.repository.files.snapshot import SnapshotAtlasRepository
from app.usecase.airports import AirportQueries

started=monotonic()
r=ClickHouseReader(os.environ['CLICKHOUSE_URL'],os.environ['CLICKHOUSE_USER'],os.environ['CLICKHOUSE_PASSWORD'])
snapshot=ClickHouseGraphSnapshot(r)
report={}
for name in ('nodes','edges'):
 table=snapshot.arrays(name)
 old=pq.read_table(Path('data/graph_ru')/(name+'.parquet'))
 if name=='edges':
  order=np.lexsort(tuple(old[k].to_numpy() for k in ('km','h','dst','src','way_idx')))
  actual_order=np.lexsort(tuple(table[k] for k in ('km','h','dst','src','way_idx')))
  table={k:v[actual_order] for k,v in table.items()}
 else:order=np.arange(len(old))
 for column,values in table.items():
  if column=='node' and column not in old.column_names:source=np.arange(len(old))
  else:source=old[column].to_numpy()[order]
  assert np.array_equal(values,source,equal_nan=True),(name,column)
 report[name]={'rows':len(old),'columns':list(table),'exact':True}
 print(name,'exact',len(old),flush=True)
 del table,old,order
with duckdb.connect('data/casechamp.duckdb',read_only=True) as con:
 region='Владимирская область'
 expected=con.execute("SELECT point_id,city,road_h FROM np_city_times WHERE season='road' AND point_id IN (SELECT point_id FROM idx_np WHERE season='road' AND region=?)",[region]).fetchall()
 actual=snapshot.read('delta_times',{'region':region})
 assert sorted(expected)==sorted(actual)
 report['regional_matrix']={'rows':len(actual),'exact':True,'infinities':sum(np.isinf(r[2]) for r in actual)}
 print('regional matrix exact',len(actual),flush=True)
source=SnapshotAtlasRepository(Path('frontend/atlas/public'),Path('data'))
atlas=ClickHouseAtlasRepository(r)
airport_old=AirportQueries(FileAirportRepository(Path('frontend/atlas/public')),source).result
airport_new=AirportQueries(ClickHouseAirportRepository(atlas),atlas).result
assert airport_old==airport_new
report['airports']={'exact':True,'airports':len(airport_new.airports),'assignments':len(airport_new.assignments)}
report['seconds']=monotonic()-started
Path('work/clickhouse-migration/graph-comparison.json').write_text(json.dumps(report,default=int,indent=2))
print(report,flush=True)
