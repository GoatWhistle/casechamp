import json
import sys
from pathlib import Path

import duckdb
import osmium

cases = {'central': '28756000051', 'northwestern': '41609465101'}
label = sys.argv[1]
identifier = cases[label]
con = duckdb.connect()
row = con.execute("select p.point_id,p.lat,p.lon,p.population,p.snap_km,n.lat,n.lon from 'data/graph_ru/points.parquet' p join 'data/graph_ru/nodes.parquet' n using(node) where p.point_id=?", [identifier]).fetchone()
point_id, lat, lon, population, snap, target_lat, target_lon = row
start=(lon,lat)
end=(target_lon,target_lat)
margin=0.02
box=(min(lon,target_lon)-margin,min(lat,target_lat)-margin,max(lon,target_lon)+margin,max(lat,target_lat)+margin)
def cross(a,b,c):
    return (b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])
def intersects(a,b,c,d):
    return cross(a,b,c)*cross(a,b,d)<0 and cross(c,d,a)*cross(c,d,b)<0
class Water(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.crossings=[]
        self.examined=0
    def way(self,way):
        kind=way.tags.get('waterway')
        if kind not in {'river','stream','canal','drain','ditch'}:
            return
        nodes=[(n.lon,n.lat) for n in way.nodes if n.location.valid()]
        if len(nodes)<2:
            return
        if max(p[0] for p in nodes)<box[0] or min(p[0] for p in nodes)>box[2] or max(p[1] for p in nodes)<box[1] or min(p[1] for p in nodes)>box[3]:
            return
        self.examined+=1
        if any(intersects(start,end,a,b) for a,b in zip(nodes,nodes[1:])):
            self.crossings.append({'osm_way_id':way.id,'waterway':kind,'name':way.tags.get('name'),'tunnel':way.tags.get('tunnel'),'intermittent':way.tags.get('intermittent')})
handler=Water()
handler.apply_file(str(Path('data/raw/osm_russia') / f'{label}.osm.pbf'),locations=True,idx='flex_mem')
print(json.dumps({'point_id':point_id,'population':population,'settlement':{'lat':lat,'lon':lon},'anchor':{'lat':target_lat,'lon':target_lon},'snap_km':snap,'source':label+'.osm.pbf','water_ways_in_bbox':handler.examined,'crossing_candidates':handler.crossings,'scope':'proper segment intersections only; not proof of impassability or route existence'},ensure_ascii=False,indent=2))
