import argparse
import json
import os
import time
from dataclasses import asdict
from pathlib import Path

from analytics.client import ClickHouse
from app.domain.normative.index import IndexValue, reference_index_values
from app.domain.normative.measurement_definition import MeasurementDefinition
from app.domain.normative.model import AccessRow
from app.domain.normative.scenario_index import ScenarioIndex, scenario_policy
from app.repository.clickhouse.client import ClickHouseReader
from import_national_inventory import insert_batch

ROOT = Path(__file__).resolve().parents[1]


def aggregate(reader, run_id, policy, expected):
    column = 'distance_metres' if policy.unit == 'metres' else 'minutes'
    stages = {'baseline': [], 'scenario': []}
    for threshold in policy.thresholds:
        rows = reader.rows(
            f'SELECT stage,count() AS n,count({column}) AS measured,count(population) AS population_known,'
            f'sum(population) AS residents,sumIf(population,{column}<={{threshold:Float64}}) AS included,'
            f'countIf({column}<={{threshold:Float64}}) AS within FROM plexus_normative.regional_measurements_rows '
            'WHERE run_id={run:String} GROUP BY stage',
            {'threshold': threshold, 'run': run_id},
        )
        for row in rows:
            stage = row['stage']
            if stage not in stages or row['n'] != expected[stage]:
                raise ValueError('Scenario source snapshot is incomplete')
            population = row['residents'] if row['population_known'] == row['n'] else None
            within_population = (row['included'] or 0) if population is not None else None
            stages[stage].append(IndexValue(
                threshold, row['n'], row['measured'], row['within'], row['n']-row['measured'],
                100*row['within']/row['n'] if row['n'] else None,
                population, within_population,
                100*within_population/population if population else None,
            ))
    if any(len(rows) != len(policy.thresholds) for rows in stages.values()):
        raise ValueError('Scenario source stages are missing')
    return stages['baseline'], stages['scenario']


def calculate(client, reader, head):
    run = head['run_id']
    if not run.isalnum() or len(run) != 32:
        raise ValueError('Unexpected measurement identifier')
    policy = scenario_policy(head['criterion_id'])
    payload = json.loads(client.request(
        f"SELECT payload FROM plexus_normative.regional_measurements WHERE id='{run}' LIMIT 1 SETTINGS max_threads=1,max_block_size=1 FORMAT RawBLOB"
    ))
    if payload['mode'] != policy.mode or payload['unit'] != policy.unit:
        raise ValueError('Scenario and saved transport model differ')
    definition = MeasurementDefinition(payload.get('measurement_definition', 'single_reference_point'))
    if definition != MeasurementDefinition.SINGLE_REFERENCE_POINT:
        raise ValueError('Scenario requires a single reference measurement')
    if policy.fire_speed_kmh is not None and (payload.get('fire_profile') or {}).get('speed_kmh') != policy.fire_speed_kmh:
        raise ValueError('Scenario fire speed differs from saved routing')
    if payload.get('snapshot_storage') == 'regional_arrow_v1':
        baseline, scenario = aggregate(reader, run, policy, payload['snapshot_counts'])
    else:
        baseline = reference_index_values([AccessRow(**r) for r in payload['baseline_rows']], policy.unit, policy.thresholds)
        scenario = reference_index_values([AccessRow(**r) for r in payload['rows']], policy.unit, policy.thresholds)
    return ScenarioIndex(head['region_id'], head['criterion_id'], run, payload['saved_at'], policy, baseline, scenario, definition)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--watch', action='store_true')
    parser.add_argument('--criteria', nargs='+', default=['N03', 'N05', 'N06', 'N07', 'N08', 'N09'])
    args = parser.parse_args()
    if any(c not in {f'N{i:02}' for i in range(1, 10)} for c in args.criteria):
        raise ValueError('Unknown scenario criterion')
    client = ClickHouse()
    reader = ClickHouseReader(os.environ.get('CLICKHOUSE_URL', 'http://127.0.0.1:18123'), os.environ.get('CLICKHOUSE_USER', 'plexus'), os.environ['CLICKHOUSE_PASSWORD'], max_threads=1, max_block_size=8192)
    for sql in (ROOT/'infra/clickhouse/normative-scenario-indices.sql').read_text().split(';'):
        if sql.strip():client.request(sql)
    while True:
        heads = reader.rows('SELECT region_id,criterion_id,argMax(id,tuple(saved_at,id)) AS run_id FROM plexus_normative.regional_measurements GROUP BY region_id,criterion_id', {})
        existing = {(r['region_id'],r['criterion_id']):(r['run_id'],r['policy_sha256']) for r in reader.rows('SELECT region_id,criterion_id,run_id,policy_sha256 FROM plexus_normative.scenario_index_summaries FINAL', {})}
        count, errors = 0, 0
        for head in sorted(heads, key=lambda r:(r['criterion_id']=='N03',r['criterion_id'],r['region_id'])):
            criterion = head['criterion_id'];region = head['region_id']
            if criterion not in args.criteria:continue
            policy = scenario_policy(criterion)
            if existing.get((region,criterion)) == (head['run_id'],policy.definition_sha256):continue
            try:
                result = calculate(client,reader,head)
                record = {'region_id':region,'criterion_id':criterion,'run_id':result.run_id,'policy_sha256':policy.definition_sha256,'payload':json.dumps(asdict(result),allow_nan=False),'publication_version':time.time_ns()}
                insert_batch(client,'plexus_normative.scenario_index_summaries',[json.dumps(record)])
                count+=1
                print('published scenario index',region,criterion,result.run_id,flush=True)
            except Exception as error:
                errors+=1;print('scenario index failed',region,criterion,type(error).__name__,str(error)[:400],flush=True)
        print('scenario publication pass complete',count,'failed',errors,flush=True)
        if not args.watch:break
        time.sleep(15)


if __name__ == '__main__':main()
