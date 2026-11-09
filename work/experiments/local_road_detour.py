import json
import math
import sys
from pathlib import Path

import duckdb
import numpy as np
import pyarrow.parquet as pq
from scipy.spatial import cKDTree
from scipy.sparse.csgraph import dijkstra

sys.path.insert(0,'etl')
from graphlib import build_csr

ids={'central':'28756000051','northwestern':'41609465101'}
label=sys.argv[1]
point_id=sys.argv[3] if len(sys.argv)>3 else ids[label]
c=duckdb.connect()
point=c.execute("select p.point_id,p.lat,p.lon,p.snap_km,n.osm_node,n.lat,n.lon from 'data/graph_ru/points.parquet' p join 'data/graph_ru/nodes.parquet' n using(node) where p.point_id=?",[point_id]).fetchone()
pid,lat,lon,snap,target_id,target_lat,target_lon=point
margin=float(sys.argv[2]) if len(sys.argv)>2 else .12
box=(min(lat,target_lat)-margin,max(lat,target_lat)+margin,min(lon,target_lon)-margin,max(lon,target_lon)+margin)
ways=[]
columns=['way_id','highway','name','source_tags','nodes','lat','lon','is_bridge','is_ferry','operating_season']
for batch in pq.ParquetFile(f'data/osm_ways/{label}.parquet').iter_batches(batch_size=5000,columns=columns):
 for row in batch.to_pylist():
  if not row['nodes'] or row['is_ferry']:
   continue
  if not any(box[0]<=la<=box[1] and box[2]<=lo<=box[3] for la,lo in zip(row['lat'],row['lon'])):
   continue
  tags=json.loads(row['source_tags'] or '{}')
  if any(tags.get(k) in ('no','private') for k in ('access','vehicle','motor_vehicle','motorcar')):
   continue
  ways.append(row)
coords={}
for w in ways:
 for node,la,lo in zip(w['nodes'],w['lat'],w['lon']):
  coords[node]=(la,lo)
keys=list(coords)
idx={key:i for i,key in enumerate(keys)}
def xyz(lat,lon):
 lat,lon=np.radians(lat),np.radians(lon)
 return np.column_stack((np.cos(lat)*np.cos(lon),np.cos(lat)*np.sin(lon),np.sin(lat)))
arr=np.array([coords[x] for x in keys]); tree=cKDTree(xyz(arr[:,0],arr[:,1])); distance,nearest=tree.query(xyz(np.array([lat]),np.array([lon])))
nearest_id=keys[int(nearest[0])]
near_km=float(12742*np.arcsin(min(1,float(distance[0])/2)))
def hav(a,b):
 la1,lo1,la2,lo2=map(math.radians,(a[0],a[1],b[0],b[1]))
 x=math.sin((la2-la1)/2)**2+math.cos(la1)*math.cos(la2)*math.sin((lo2-lo1)/2)**2
 return 12742*math.asin(min(1,math.sqrt(x)))
a=[];b=[];d=[];way_edge={}
for w in ways:
 for first,second in zip(w['nodes'],w['nodes'][1:]):
  if first not in coords or second not in coords or first==second: continue
  dist=hav(coords[first],coords[second]); i,j=idx[first],idx[second]
  a.extend((i,j)); b.extend((j,i));d.extend((dist,dist))
  for pair in ((i,j),(j,i)):
   if pair not in way_edge or dist<way_edge[pair][0]: way_edge[pair]=(dist,w['way_id'],w['is_bridge'],w['name'],w['operating_season'])
if target_id not in idx:
 raise RuntimeError('target node absent from local source graph')
graph=build_csr(np.array(a),np.array(b),np.array(d),len(keys))
dist,pred=dijkstra(graph,directed=True,indices=idx[nearest_id],return_predecessors=True)
target=idx[target_id]
result={'point_id':pid,'pbf_extract':label,'selection':f'ways having at least one vertex in bounding box expanded {margin} degrees; entire selected way included','way_count':len(ways),'nodes':len(keys),'nodes_reachable_from_nearest_local':int(np.isfinite(dist).sum()),'nearest_local_ways':[{'way_id':w['way_id'],'highway':w['highway'],'name':w['name']} for w in ways if nearest_id in w['nodes']],'settlement_snap_to_local_road_km':near_km,'national_straight_snap_km':snap,'nearest_local_osm_node':nearest_id,'national_anchor_osm_node':int(target_id),'directions_ignored':True,'ferries_and_explicitly_forbidden_access_excluded':True,'network_distance_km':None,'bridge_ways':[],'seasonal_ways':[]}
if np.isfinite(dist[target]):
 result['network_distance_km']=float(dist[target]); path=[]; cursor=target
 while cursor!=idx[nearest_id]:
  prev=int(pred[cursor]); assert prev>=0
  path.append(way_edge[(prev,cursor)]);cursor=prev
 result['path_segment_count']=len(path)
 result['bridge_ways']=list({(v[1],v[3]) for v in path if v[2]})
 result['seasonal_ways']=list({(v[1],v[4]) for v in path if v[4]!='all'})
print(json.dumps(result,ensure_ascii=False,indent=2))
