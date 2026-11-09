import json, sys
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from scipy.sparse.csgraph import dijkstra
sys.path.insert(0,'etl')
from graphlib import build_csr
base='data/pilot_graph_build/'
e=pq.read_table(base+'edges.parquet').to_pandas()
w=pq.read_table(base+'ways.parquet').to_pandas()
p=pq.read_table(base+'points.parquet').to_pandas().set_index('point_id')
n=pq.read_metadata(base+'nodes.parquet').num_rows
src=p.loc['93643425101'];dst=p.loc['93701000001'];snap=(src.snap_km+dst.snap_km)/15
for season in ('summer','winter'):
 for remove in (False,True):
  allowed=w.operating_season.isin(['all',season]).values.copy()
  if remove: allowed &= w.way_id.ne(316392825).values
  sub=e[allowed[e.way_idx.values]]
  for directed in (True,False):
   g=build_csr(sub.src.values,sub.dst.values,sub.h.values,n,undirected=not directed)
   d=dijkstra(g,directed=True,indices=int(src.node),limit=np.inf)
   print(json.dumps({'season':season,'remove_way':316392825 if remove else None,'directed':directed,'road_hours':float(d[int(dst.node)]+snap) if np.isfinite(d[int(dst.node)]) else None,'source_snap_km':float(src.snap_km),'target_snap_km':float(dst.snap_km),'edges':len(sub)}))
