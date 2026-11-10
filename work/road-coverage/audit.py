import json
from datetime import datetime, timezone
from pathlib import Path

import duckdb
import pandas as pd
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent


def main() -> None:
    atlas = json.loads((ROOT / 'frontend/atlas/public/atlas.json').read_text())
    regions = pd.DataFrame(atlas['regions'])[['id', 'name']]
    points = pq.read_table(ROOT / 'data/graph_ru/points.parquet').to_pandas()
    with duckdb.connect(str(ROOT / 'data/casechamp.duckdb'), read_only=True) as con:
        names = con.sql("select oktmo point_id, object_name from stg_settlements where object_level='Населенный пункт'").df()
        access = con.sql("select point_id,t_nearest_city_h from np_access where season='road'").df()
        region_names = dict(con.sql("select oktmo,region from stg_settlements where object_level='Регион'").fetchall())
    points = points.merge(names, on='point_id', validate='one_to_one')
    points = points.merge(access, on='point_id', how='left', validate='one_to_one', indicator=True)
    points['no_market_path'] = points.t_nearest_city_h.isna()
    rows = []
    for region in regions.itertuples():
        selected = points[points.region == region_names[region.id]]
        assert len(selected), region.name
        unbound = ~selected.on_road
        no_market = selected.no_market_path
        rows.append({
            'region_id': region.id, 'region': region_names[region.id],
            'points': len(selected), 'population': int(selected.population.sum()),
            'unbound_points': int(unbound.sum()),
            'unbound_population': int(selected.loc[unbound, 'population'].sum()),
            'no_market_points': int(no_market.sum()),
            'no_market_population': int(selected.loc[no_market, 'population'].sum()),
            'missing_access_rows': int((selected['_merge'] != 'both').sum()),
            'components_with_settlements': int(selected.loc[selected.on_road, 'comp'].nunique()),
            'status': 'requires_source_check' if no_market.any() else 'connected_source_completeness_unverified',
        })
    frame = pd.DataFrame(rows).sort_values('no_market_population', ascending=False)
    assert len(frame) == 82 and frame.region_id.nunique() == 82
    frame.to_csv(OUT / 'regions-before.csv', index=False)
    flagged = points[points.region.isin(frame.region) & points.no_market_path]
    flagged.drop(columns='_merge').to_csv(OUT / 'settlements-before.csv', index=False)
    report = {
        'observed_at': datetime.now(timezone.utc).isoformat(),
        'regions_checked': len(frame), 'regions_with_unbound_points': int((frame.unbound_points > 0).sum()),
        'regions_without_market_path': int((frame.no_market_points > 0).sum()),
        'points': int(frame.points.sum()), 'unbound_points': int(frame.unbound_points.sum()),
        'unbound_population': int(frame.unbound_population.sum()),
        'no_market_points': int(frame.no_market_points.sum()),
        'no_market_population': int(frame.no_market_population.sum()),
        'limitation': 'Graph and DuckDB are the legacy release; published five-scenario indices have different provenance. Connectivity is not source completeness.',
        'regions': rows,
    }
    (OUT / 'baseline.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n')
    print(json.dumps({k: v for k, v in report.items() if k != 'regions'}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
