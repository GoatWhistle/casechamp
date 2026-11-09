import json
import math
import duckdb
import numpy as np
import pyarrow as pa

con=duckdb.connect('data/casechamp.duckdb',read_only=True)
sample=con.sql("""with candidates as (
 select point_id,region,population,reachable_markets,
 row_number() over(partition by region order by population desc,point_id) as large_rank,
 row_number() over(partition by region order by case when population>0 then population else null end asc nulls last,point_id) as small_rank,
 row_number() over(partition by region order by case when reachable_markets=0 then 0 else 1 end,point_id) as unlinked_rank
 from idx_np where season='road')
 select * from candidates where large_rank=1 or small_rank=1 or (reachable_markets=0 and unlinked_rank=1)""").df()
con.register('sample_points',pa.table({'point_id':pa.array(sample.point_id.tolist(),type=pa.string())}))
stored=con.sql('select n.season,n.point_id,n.region,n.population,n.reachable_markets,n.hansen_1h,n.hansen_2h,n.hansen_4h,n.hansen_idx from idx_np n join sample_points s using(point_id)').df()
assert len(stored)==len(sample)*5 and stored.region.nunique()==82
trips=con.sql('select t.season,t.point_id,t.city,t.best_h,m.population from np_city_times t join sample_points s using(point_id) join market_cities m using(city)').df()
assert not trips.duplicated(['season','point_id','city']).any()
assert np.isfinite(trips.best_h).all() and (trips.best_h>=0).all() and (trips.population>0).all()
groups={(season,point):g for (season,point),g in trips.groupby(['season','point_id'],sort=False)}
base=con.sql('select normalization_base from index_model_metadata').fetchone()[0]
errors=[]
for row in stored.itertuples(index=False):
 g=groups.get((row.season,row.point_id))
 times=np.array([],dtype=float) if g is None else g.best_h.to_numpy(dtype=float)
 populations=np.array([],dtype=float) if g is None else g.population.to_numpy(dtype=float)
 assert len(times)==row.reachable_markets
 for half in (1,2,4):
  expected=math.fsum(float(m)*math.exp(-math.log(2)*float(t)/half) for t,m in zip(times,populations))
  actual=getattr(row,f'hansen_{half}h')
  error=abs(expected-actual)
  if not math.isclose(expected,actual,rel_tol=1e-10,abs_tol=1e-6):
   errors.append({'season':row.season,'point_id':row.point_id,'half_life_h':half,'reference':expected,'stored':actual,'error':error})
 expected_index=100*row.hansen_2h/base
 if not math.isclose(expected_index,row.hansen_idx,rel_tol=1e-10,abs_tol=1e-8):
  errors.append({'season':row.season,'point_id':row.point_id,'kind':'normalization','reference':expected_index,'stored':row.hansen_idx})
report={'sample_origins':len(sample),'regions':int(sample.region.nunique()),'sample_rows':len(stored),'independent_formula_checks':len(stored)*3,'normalization_checks':len(stored),'trip_rows':len(trips),'zero_route_rows':int((stored.reachable_markets==0).sum()),'sample_strategy':'largest and smallest positive-population settlement per region plus one no-market road point where present; overlapping picks deduplicated','tolerance':'Hansen rel 1e-10, abs 1e-6; normalized rel 1e-10, abs 1e-8','input':'data/casechamp.duckdb read-only','errors':errors}
print(json.dumps(report,ensure_ascii=False,indent=2,allow_nan=False))
if errors: raise SystemExit(1)
