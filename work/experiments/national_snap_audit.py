import json
import duckdb

con = duckdb.connect()
con.execute('SET threads=4')
summary = con.sql("""with p as (select * from 'data/graph_ru/points.parquet'),
n as (select node,lat nlat,lon nlon,comp ncomp from 'data/graph_ru/nodes.parquet'),
j as (select p.*,n.nlat,n.ncomp,2*6371*asin(sqrt(least(1.0,pow(sin(radians(n.nlat-p.lat)/2),2)+cos(radians(p.lat))*cos(radians(n.nlat))*pow(sin(radians(n.nlon-p.lon)/2),2)))) geo_km from p left join n on p.node=n.node)
select count(*) total, count(distinct point_id) unique_points,
count(*) filter(where on_road) road_points, count(*) filter(where not on_road) no_road_points,
sum(population) filter(where not on_road) no_road_population,
count(*) filter(where on_road and nlat is null) missing_node,
count(*) filter(where on_road and comp!=ncomp) component_mismatch,
count(*) filter(where on_road and (snap_km>5 or node<0)) invalid_anchor,
count(*) filter(where on_road and abs(geo_km-snap_km)>0.01) distance_mismatch,
max(abs(geo_km-snap_km)) filter(where on_road) max_distance_error_km,
quantile_cont(snap_km,0.5) filter(where on_road) median_km,
quantile_cont(snap_km,0.95) filter(where on_road) p95_km,
quantile_cont(snap_km,0.99) filter(where on_road) p99_km,
count(*) filter(where on_road and snap_km>1) points_over_1_km,
sum(population) filter(where on_road and snap_km>1) population_over_1_km,
count(*) filter(where on_road and snap_km>2) points_over_2_km,
count(distinct comp) filter(where on_road) components
from j""").df().iloc[0].to_dict()
components=con.sql("select comp,count(*) settlements,sum(population) population from 'data/graph_ru/points.parquet' where on_road group by comp order by population desc").df()
regions=con.sql("select region,count(*) settlements,sum(population) population from 'data/graph_ru/points.parquet' where not on_road group by region order by population desc").df()
assert summary['total']==summary['unique_points']==155747
assert summary['missing_node']==summary['component_mismatch']==summary['invalid_anchor']==summary['distance_mismatch']==0
print(json.dumps({'scope':'all graph input settlements, including partial federal city points, not only 82-region index','summary':summary,'components':components.to_dict('records'),'regions_without_road_anchor':regions.to_dict('records'),'limitation':'straight-line snap and weak connectivity do not demonstrate usable roads, seasonal connectivity or accessibility from the settlement'},ensure_ascii=False,indent=2,default=lambda x:x.item(),allow_nan=False))
