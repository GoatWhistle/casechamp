import json
import duckdb

con = duckdb.connect('data/casechamp.duckdb', read_only=True)
point = '28756000051'
assert con.execute('select count(*) from market_cities where oktmo=?', [point]).fetchone()[0] == 0
links = con.execute('select season, mode, count(*) from manual_links_ru where from_id=? or to_id=? group by season,mode order by season,mode', [point,point]).fetchall()
rows = con.execute("""select n.season,n.population point_population,n.hansen_idx point_hansen,
 r.population region_population,r.hansen_idx region_hansen,r.covered_population
 from idx_np n join idx_region r on n.season=r.season and n.region=r.region
 where n.point_id=? order by n.season""", [point]).df()
assert len(rows)==5 and set(rows.season)=={'road','road_summer','road_winter','summer','winter'}
output=[]
for row in rows.itertuples(index=False):
 reduction=float(row.point_population*row.point_hansen/row.region_population)
 output.append({'season':row.season,'point_population':int(row.point_population),'region_population':int(row.region_population),'point_hansen':float(row.point_hansen),'regional_baseline':float(row.region_hansen),'stress_point_hansen':0.0,'stress_region':float(row.region_hansen-reduction),'delta_index_points':-reduction,'relative_change_percent':-100*reduction/row.region_hansen,'coverage_baseline_percent':100*float(row.covered_population)/float(row.region_population),'coverage_stress_percent':100*(float(row.covered_population)-float(row.point_population))/float(row.region_population)})
print(json.dumps({'point_id':point,'regional_normalization':'original fixed road baseline; not recalculated','method':'replace the single point contribution and coverage with zero; all other points fixed','manual_links':[{'season':s,'mode':m,'count':n} for s,m,n in links],'values':output},ensure_ascii=False,indent=2))
