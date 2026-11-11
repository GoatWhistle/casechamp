import json
import os
from pathlib import Path
from time import monotonic, sleep
from urllib.request import Request, urlopen

from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.graph_queries import QUERIES
from app.settings import load_settings


def request(path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    with urlopen(Request('http://127.0.0.1:8817/api/v1/road-stress-tests'+path, data=data,
                         headers={'Content-Type':'application/json'}), timeout=180) as response:
        return json.load(response)


def main():
    config = load_settings(os.environ)
    reader = ClickHouseReader(config.clickhouse_url, config.clickhouse_user, config.clickhouse_password)
    records = []
    parent = None
    for reference in ['М-10', 'М-11', 'Р-257']:
        rows = reader.rows(QUERIES['references'], {'references': [reference]})
        ids = sorted({int(row['way_id']) for row in rows})
        if not ids:
            raise RuntimeError('Missing reference '+reference)
        started = monotonic()
        body = {'way_ids':ids}
        if reference == 'М-11':
            body['parent_id'] = parent
        job = request('',body)
        print(reference, len(ids), job['id'], flush=True)
        while job['status'] in ['queued','running']:
            sleep(5)
            job = request('/'+job['id'])
            print(job['stage'],job['completed'], flush=True)
        if job['status'] != 'completed':
            raise RuntimeError(str(job))
        impacts = request('/'+job['id']+'/impacts?limit=3')
        records.append({'reference':reference,'job':job,'elapsed_seconds':monotonic()-started,'sample':impacts})
        Path('work/road-stress/scenario-validation.json').write_text(json.dumps(records,ensure_ascii=False,indent=2))
        parent = job['id']
        print('Completed',records[-1]['elapsed_seconds'],len(job['regions']),flush=True)


if __name__ == '__main__':
    main()
