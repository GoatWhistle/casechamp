import json
import math
import duckdb

con = duckdb.connect('data/casechamp.duckdb', read_only=True)
ids = ['54618416111', '54618422101']
rows = con.execute('''select s.oktmo, s.settlement, s.mun_lower, s.population, s.latitude, s.longitude,
                             n.hansen_idx, n.reachable_markets
                      from stg_settlements s join idx_np n on n.point_id=s.oktmo
                      where s.oktmo in (?, ?) and n.season='road' order by s.oktmo''', ids).df().to_dict('records')
assert len(rows) == 2
for point in ids:
    assert con.execute('select count(*) from market_cities where oktmo=?', [point]).fetchone()[0] == 0
    assert con.execute('select count(*) from manual_links_ru where from_id=? or to_id=?', [point, point]).fetchone()[0] == 0
region_population, baseline = con.execute("select population,hansen_idx from idx_region where region='Орловская область' and season='road'").fetchone()
a, b = rows
lat1, lon1, lat2, lon2 = map(math.radians, (a['latitude'], a['longitude'], b['latitude'], b['longitude']))
x = math.sin((lat2-lat1)/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin((lon2-lon1)/2)**2
distance = 12742 * math.asin(min(1, math.sqrt(x)))
delta = b['population'] * (a['hansen_idx'] - b['hansen_idx']) / region_population
print(json.dumps({'rows':rows,'separation_km':distance,'regional_population':region_population,
                  'regional_baseline':baseline,'fixed_normalization_swap_stress':baseline+delta,
                  'delta_index_points':delta,'relative_change_percent':100*delta/baseline,
                  'method':'replace only the 517-person origin contribution with the stored index of the other coordinate, other values and normalization fixed; not a recomputation'},ensure_ascii=False,indent=2))
