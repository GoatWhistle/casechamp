import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from analytics.client import ClickHouse
from app.domain.normative.index import validate_index_basis
from app.repository.clickhouse.index_basis_record import basis_from_record
from import_national_inventory import insert_batch

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    rows = json.loads((ROOT / 'datasets/normative-index-bases.json').read_text())
    prepared = []
    for row in rows:
        digest = hashlib.sha256(json.dumps(row, sort_keys=True).encode()).hexdigest()
        basis = basis_from_record({**row, 'definition_sha256': digest})
        validate_index_basis(basis)
        record = {**row, 'definition_sha256': digest, 'updated_at': datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S.%f')}
        for key in ('review', 'intervals'):
            if key in record:
                record[key] = json.dumps(record[key], ensure_ascii=False)
        prepared.append(json.dumps(record))
    client = ClickHouse()
    for statement in (ROOT / 'infra/clickhouse/normative-index-bases.sql').read_text().split(';'):
        if statement.strip():
            client.request(statement)
    insert_batch(client, 'plexus_normative.index_bases', prepared)
    print('Index bases imported', len(rows))


if __name__ == '__main__':
    main()
