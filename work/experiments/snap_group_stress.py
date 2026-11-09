import json
from pathlib import Path

import duckdb

paths = sorted(Path('work/experiments').glob('snap-water-scan-*.json'))
assert len(paths) == 10
points = {}
for path in paths:
    result = json.loads(path.read_text())
    assert result['candidate_segments'] == 1950
    for row in result['matches']:
        previous = points.get(row['point_id'])
        if previous:
            assert previous['population'] == row['population'] and previous['region'] == row['region']
        points[row['point_id']] = row
assert len(points) == 765
con = duckdb.connect('data/casechamp.duckdb', read_only=True)
con.execute('create temporary table selected_ids(point_id varchar)')
con.executemany('insert into selected_ids values (?)', [(point_id,) for point_id in sorted(points)])
rows = con.execute('''
select n.region, count(*) candidates, sum(n.population) candidate_population,
       sum(n.population*n.hansen_idx) candidate_weighted_sum,
       count(*) filter (where n.reachable_markets > 0) candidates_with_market
from idx_np n join selected_ids s using(point_id)
where n.season='road'
group by n.region
''').df()
regions = con.execute("select region,population,hansen_idx from idx_region where season='road'").df()
assert len(regions) == 82
baseline_check = con.execute('''
select region, sum(population*hansen_idx)/sum(population) weighted_mean
from idx_np where season='road' group by region
''').df()
check = regions.merge(baseline_check, on='region', validate='one_to_one')
assert (check.hansen_idx - check.weighted_mean).abs().max() < 1e-8
out = regions.merge(rows, on='region', how='left', validate='one_to_one').fillna(0)
out['stress_hansen'] = out.hansen_idx - out.candidate_weighted_sum / out.population
out['delta_points'] = out.stress_hansen - out.hansen_idx
out['change_percent'] = 100 * out.delta_points / out.hansen_idx
out['rank_baseline'] = out.hansen_idx.rank(method='min', ascending=False).astype(int)
out['rank_stress'] = out.stress_hansen.rank(method='min', ascending=False).astype(int)
out = out.sort_values('delta_points')
for column in ['population', 'candidate_population', 'candidates', 'candidates_with_market', 'rank_baseline', 'rank_stress']:
    out[column] = out[column].astype(int)
print(json.dumps({'scope':'road scenario, 82 regions, 765 candidates from ten extracts',
                  'method':'set each candidate origin Hansen index to zero simultaneously, keep all other origin values, population denominator and original normalization fixed',
                  'limitations':'conditional accounting stress only; does not remove connectors, recompute routes or normalizer, quantify true error, or establish an upper bound on network impacts',
                  'unique_candidates':len(points),
                  'candidates_in_index':int(out.candidates.sum()),
                  'candidate_population_in_index':int(out.candidate_population.sum()),
                  'regions':out.to_dict('records')},ensure_ascii=False,indent=2,allow_nan=False))
