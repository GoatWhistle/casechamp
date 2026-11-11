import json
import os
from dataclasses import asdict
from pathlib import Path
from time import monotonic

from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.stress import ClickHouseStressStore
from app.settings import load_settings

settings = load_settings(os.environ)
reader = ClickHouseReader(settings.clickhouse_url, settings.clickhouse_user, settings.clickhouse_password)
store = ClickHouseStressStore(reader)
job_id = '95c3a442bf544d118fac5403cf80eede'
job = next(j for j in store.load() if j.id == job_id)
assert job.status == 'completed'
output = []
for region in ['Новгородская область', 'Тверская область']:
    start = monotonic()
    metrics = store.consequences(job_id, region)
    result = {'job_id': job_id, 'graph_version': job.version, 'way_count': len(job.way_ids),
              'totals': asdict(store.totals(job_id, region)), 'consequences': asdict(metrics),
              'elapsed_seconds': monotonic() - start}
    output.append(result)
    print(json.dumps({'region':region,'lost':metrics.lost_connections,
                     'delays':[asdict(b) for b in metrics.delay_exposure],
                     'nearby':asdict(metrics.nearby_access)},ensure_ascii=False),flush=True)
Path('work/regional-consequences/real-results.json').write_text(json.dumps(output,ensure_ascii=False,indent=2))
for result in output:
    report = result['consequences']
    region = report['region']
    bands = {t: [0, 0] for t in (30, 60, 120)}
    before = after = 0.0
    comparable = lost = changed = crossing = crossing_points = crossing_residents = 0
    count = offset = 0
    while True:
        batch = store.impacts(job_id, region, offset, 200)
        if not batch:
            break
        for impact in batch:
            count += 1
            for threshold in bands:
                if impact.delay_minutes >= threshold:
                    bands[threshold][0] += 1
                    bands[threshold][1] += impact.point.population
            point_crossing = False
            for route in impact.markets:
                if route.before_hours > 2:
                    continue
                changed += 1
                if route.after_hours is None:
                    lost += 1
                else:
                    comparable += 1
                    before += route.before_hours * 60
                    after += route.after_hours * 60
                if route.after_hours is None or route.after_hours > 2:
                    crossing += 1
                    point_crossing = True
            if point_crossing:
                crossing_points += 1
                crossing_residents += impact.point.population
        offset += len(batch)
    assert count == result['totals']['affected_points']
    nearby = report['nearby_access']
    assert (changed,lost,comparable,crossing,crossing_points,crossing_residents) == (
        nearby['changed_connections'], nearby['lost_connections'],nearby['comparable_connections'],
        nearby['connections_crossing_threshold'],nearby['settlements_crossing_threshold'],nearby['residents_crossing_threshold'])
    assert abs(before/comparable - nearby['mean_before_minutes']) < 1e-6
    assert abs(after/comparable - nearby['mean_after_minutes']) < 1e-6
    for band in report['delay_exposure']:
        assert bands[band['threshold_minutes']] == [band['settlements'],band['residents']]
    result['independent_check'] = {'all_impacted_points_checked': count, 'passed':True}
    print('independent regional check',region,count,flush=True)
Path('work/regional-consequences/real-results.json').write_text(json.dumps(output,ensure_ascii=False,indent=2))
