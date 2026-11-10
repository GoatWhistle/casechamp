import json
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
DEST = ROOT / 'data/road-refresh'
OUT = Path(__file__).resolve().parent


def main():
    regions = pd.DataFrame(json.loads((DEST / 'atlas-input.json').read_text())['regions'])[['id', 'name']]
    points = pq.read_table(DEST / 'graph/points.parquet').to_pandas()
    with duckdb.connect(str(DEST / 'casechamp.duckdb'), read_only=True) as con:
        names = con.sql("SELECT oktmo point_id,object_name FROM stg_settlements WHERE object_level='Населенный пункт'").df()
        access = con.sql("SELECT point_id,t_nearest_city_h FROM np_access WHERE season='road'").df()
        region_names = dict(con.sql("SELECT oktmo,region FROM stg_settlements WHERE object_level='Регион'").fetchall())
        covered = con.sql("SELECT point_id,reachable_markets,hansen_idx FROM idx_np WHERE season='road'").df()
    points = points.merge(names, on='point_id', validate='one_to_one').merge(access, on='point_id', how='left', validate='one_to_one', indicator=True)
    points = points.merge(covered, on='point_id', how='left', validate='one_to_one')
    points['no_market_path'] = points.t_nearest_city_h.isna()
    rows = []
    for region in regions.itertuples():
        selected = points[points.region == region_names[region.id]]
        assert len(selected), region.name
        unbound, no_market = ~selected.on_road, selected.no_market_path
        rows.append(dict(region_id=region.id, region=region_names[region.id], points=len(selected),
            population=int(selected.population.sum()), unbound_points=int(unbound.sum()),
            unbound_population=int(selected.loc[unbound, 'population'].sum()),
            no_market_points=int(no_market.sum()), no_market_population=int(selected.loc[no_market, 'population'].sum()),
            missing_access_rows=int((selected['_merge'] != 'both').sum()),
            components_with_settlements=int(selected.loc[selected.on_road, 'comp'].nunique()),
            status='requires_source_check' if no_market.any() else 'connected_source_completeness_unverified'))
    frame = pd.DataFrame(rows)
    assert len(frame) == 82 and frame.region_id.nunique() == 82 and frame.missing_access_rows.sum() == 0
    before = pd.read_csv(OUT / 'regions-before.csv', dtype={'region_id': str})
    comparison = before.merge(frame, on=['region_id', 'region'], suffixes=('_before', '_after'), validate='one_to_one')
    for metric in ['unbound_points', 'unbound_population', 'no_market_points', 'no_market_population']:
        comparison[metric + '_change'] = comparison[metric + '_after'] - comparison[metric + '_before']
    comparison.sort_values('no_market_population_change').to_csv(OUT / 'regions-comparison.csv', index=False)
    frame.to_csv(OUT / 'regions-after.csv', index=False)
    scoped = points[points.region.isin(frame.region)]
    scoped[scoped.no_market_path].drop(columns='_merge').to_csv(OUT / 'settlements-after.csv', index=False)
    old_gaps = pd.read_csv(OUT / 'settlements-before.csv', dtype={'point_id': str})
    recovered = scoped[scoped.point_id.isin(old_gaps.point_id) & ~scoped.no_market_path]
    recovered.drop(columns='_merge').to_csv(OUT / 'recovered-settlements.csv', index=False)
    lost = scoped[~scoped.point_id.isin(old_gaps.point_id) & scoped.no_market_path]
    lost.drop(columns='_merge').to_csv(OUT / 'newly-disconnected.csv', index=False)
    report = dict(measured_at=datetime.now(timezone.utc).isoformat(), regions_checked=82,
        points=int(frame.points.sum()), unbound_points=int(frame.unbound_points.sum()),
        unbound_population=int(frame.unbound_population.sum()), no_market_points=int(frame.no_market_points.sum()),
        no_market_population=int(frame.no_market_population.sum()), recovered_points=len(recovered),
        recovered_population=int(recovered.population.sum()), newly_disconnected_points=len(lost),
        newly_disconnected_population=int(lost.population.sum()),
        limitation='Before uses legacy graph/scenario; after uses current five-scenario model. Connectivity changes include source, anchor and season-policy changes; index differences cannot be attributed solely to new roads.')
    (OUT / 'comparison.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
