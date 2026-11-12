import argparse
import os
import time
from datetime import UTC, datetime
from pathlib import Path

from analytics.client import ClickHouse
from app.domain.errors import DataUnavailable
from app.domain.normative.index import index_weighting
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.index_bases import ClickHouseIndexBasisRepository
from app.repository.clickhouse.index_map import ClickHouseIndexMapRepository
from app.repository.clickhouse.regional_measurements import ClickHouseRegionalMeasurementRepository
from app.usecase.normative.index_map import IndexMapQueries
from app.usecase.normative.indices import RegionalIndices

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--watch', action='store_true')
    args = parser.parse_args()
    client = ClickHouse()
    for statement in (ROOT / 'infra/clickhouse/normative-index-map.sql').read_text().split(';'):
        if statement.strip():
            client.request(statement)
    reader = ClickHouseReader(os.environ.get('CLICKHOUSE_URL', 'http://127.0.0.1:18123'), os.environ.get('CLICKHOUSE_USER', 'plexus'), os.environ['CLICKHOUSE_PASSWORD'], max_threads=1, max_block_size=8192)
    repository = ClickHouseIndexMapRepository(reader)
    summaries = IndexMapQueries(repository, lambda: datetime.now(UTC))
    indices = RegionalIndices(ClickHouseIndexBasisRepository(reader), ClickHouseRegionalMeasurementRepository(reader))
    while True:
        published = 0
        unavailable = 0
        for criterion in [f'N{i:02}' for i in range(1, 10)]:
            try:
                rows = repository.inputs(criterion)
            except DataUnavailable:
                unavailable += 1
                print("index publication storage unavailable", criterion, flush=True)
                continue
            for row in rows:
                if row.basis is None or row.run_id is None:
                    continue
                if row.summary is not None and row.summary.index is not None and row.summary.run_id == row.run_id and row.summary.definition_sha256 == row.basis.definition_sha256 and row.summary.weighting == index_weighting(criterion):
                    continue
                try:
                    index = indices.latest(row.region_id, criterion)
                    if summaries.publish(index):
                        published += 1
                        print('published index', row.region_id, criterion, index.run_id, flush=True)
                except DataUnavailable:
                    unavailable += 1
                    print("index publication storage unavailable", row.region_id, criterion, flush=True)
        print('index publication pass complete', published, 'unavailable', unavailable, flush=True)
        if not args.watch:
            if unavailable:
                raise RuntimeError("Index publication incomplete: storage unavailable for " + str(unavailable) + " inputs")
            break
        time.sleep(30)


if __name__ == '__main__':
    main()
