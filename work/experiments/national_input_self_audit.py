import json
import duckdb
import pandas as pd

con = duckdb.connect('data/casechamp.duckdb', read_only=True)
city = con.sql("""select anchor_kind,count(*) n,sum(m.population) population,
 count(*) filter(where s.oktmo is null) missing,
 count(*) filter(where s.oktmo is not null and s.population!=m.population) population_mismatch
 from market_cities m left join stg_settlements s on s.oktmo=m.oktmo and s.object_level='Населенный пункт'
 group by 1 order by 1""").df()
origins = con.sql("""select count(*) n,count(*) filter(where s.oktmo is null) missing,
 count(*) filter(where n.population!=s.population) population_mismatch,
 count(*) filter(where n.region!=s.region) region_mismatch
 from idx_np n left join stg_settlements s on s.oktmo=n.point_id and s.object_level='Населенный пункт'
 where n.season='road'""").df().iloc[0].to_dict()
assert origins['n']==155412 and origins['missing']==origins['population_mismatch']==origins['region_mismatch']==0
assert int(city.n.sum())==180 and int(city.missing.sum())==3 and int(city.population_mismatch.sum())==0
regional = con.sql("""with own as (
 select n.region,n.population origin_pop,m.population market_pop,t.best_h
 from idx_np n join market_cities m on n.point_id=m.oktmo
 join np_city_times t on t.season=n.season and t.point_id=n.point_id and t.city=m.city
 where n.season='road_summer'), self_term as (
 select region,sum(cast(origin_pop as double)*market_pop*exp(-ln(2.0)*cast(best_h as double)/2)) self_sum
 from own group by region), total as (
 select region,sum(cast(population as double)*hansen_2h) total from idx_np
 where season='road_summer' group by region)
 select t.region,t.total,coalesce(s.self_sum,0) self_sum,r.hansen_idx
 from total t left join self_term s using(region)
 join idx_region r on t.region=r.region and r.season='road_summer'""").df()
assert len(regional)==82 and (regional.total>0).all()
regional['self_pct']=100*regional.self_sum/regional.total
regional['without_self_fixed_base']=regional.hansen_idx*(1-regional.self_sum/regional.total)
regional['rank']=regional.hansen_idx.rank(ascending=False,method='min').astype(int)
regional['rank_without_self']=regional.without_self_fixed_base.rank(ascending=False,method='min').astype(int)
regional['rank_shift']=regional['rank']-regional.rank_without_self
out={'origins':origins,'market_anchor_summary':city.to_dict('records'),'method':'Remove only contribution of each target city to its own settlement; fixed road normalization; road_summer; no graph recomputation', 'region_count':len(regional),'top_self_share':regional.sort_values('self_pct',ascending=False).head(12).to_dict('records'),'largest_rank_shifts':regional.assign(abs_shift=regional.rank_shift.abs()).sort_values('abs_shift',ascending=False).head(12).drop(columns='abs_shift').to_dict('records')}
print(json.dumps(out,ensure_ascii=False,indent=2,default=lambda x: x.item(),allow_nan=False))
