import json
from pathlib import Path
import duckdb
import numpy as np
import pandas as pd

con = duckdb.connect('data/casechamp.duckdb', read_only=True)
points = con.sql('select season, point_id, region, population, hansen_idx, reachable_markets from idx_np').df()
regions = con.sql("select i.season, i.region, i.hansen_idx, i.population, i.n_np, i.covered_population, i.covered_settlements, s.oktmo region_id from idx_region i join stg_settlements s on i.region=s.region and s.object_level='Регион'").df()
exports = pd.DataFrame(json.loads(Path('frontend/atlas/public/indices.json').read_text()))
assert not points.duplicated(['season', 'point_id']).any()
assert not regions.duplicated(['season', 'region_id']).any()
assert not exports.duplicated(['season', 'region_id']).any()
records=[]
for (season, region), group in points.groupby(['season','region'], sort=True):
    weight=group.population.to_numpy(dtype=float)
    index=group.hansen_idx.to_numpy(dtype=float)
    covered=group.reachable_markets.to_numpy()>0
    total=weight.sum()
    assert total>0 and np.isfinite(index).all() and (weight>=0).all()
    records.append({'season':season,'region':region,'n':len(group),'population':int(total), 'covered_population':int(weight[covered].sum()), 'covered_settlements':int(covered.sum()), 'recomputed':float(np.average(index,weights=weight)), 'covered_only':float(np.average(index[covered],weights=weight[covered])) if weight[covered].sum() else None})
recalc=pd.DataFrame(records)
merged=regions.merge(recalc,on=['season','region'],validate='one_to_one')
assert len(merged)==len(regions)==len(exports)==410
for col, expected in [('population','population_y'),('n_np','n'),('covered_population','covered_population_y'),('covered_settlements','covered_settlements_y')]:
    original=col+'_x' if col+'_x' in merged else col
    assert (merged[original]==merged[expected]).all(),col
assert np.allclose(merged.hansen_idx,merged.recomputed,rtol=1e-11,atol=1e-11)
e=regions.merge(exports,on=['season','region_id'],validate='one_to_one',suffixes=('_db','_export'))
for col in ['hansen_idx','population','covered_population','covered_settlements']:
    assert np.allclose(e[col+'_db'],e[col+'_export'],rtol=1e-11,atol=1e-11),col
summer=merged[merged.season=='summer'].copy()
summer['coverage_pct']=100*summer.covered_population_x/summer.population_x
summer['relative_diff_pct']=100*(summer.covered_only/summer.recomputed-1)
summer['rank_all']=summer.recomputed.rank(ascending=False,method='min').astype(int)
summer['rank_covered']=summer.covered_only.rank(ascending=False,method='min').astype(int)
summer['rank_shift']=summer.rank_all-summer.rank_covered
output={'scenario_summary':points.groupby('season').apply(lambda g: {'settlements':len(g),'no_markets':int((g.reachable_markets==0).sum()),'population_no_markets':int(g.loc[g.reachable_markets==0,'population'].sum()),'zero_population_points':int((g.population==0).sum())},include_groups=False).to_dict(), 'regional_rows_checked':len(merged),'max_abs_error':float(np.max(np.abs(merged.hansen_idx-merged.recomputed))),'largest_summer_coverage_gaps':summer.sort_values('coverage_pct').head(8)[['region','coverage_pct','recomputed','covered_only','relative_diff_pct','rank_all','rank_covered','rank_shift']].to_dict('records'), 'largest_rank_shifts':summer.assign(abs_shift=summer.rank_shift.abs()).sort_values('abs_shift',ascending=False).head(8)[['region','coverage_pct','rank_all','rank_covered','rank_shift']].to_dict('records')}
print(json.dumps(output,ensure_ascii=False,indent=2,allow_nan=False))
