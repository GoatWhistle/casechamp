import json
from urllib.request import Request, urlopen
from uuid import uuid4

import pytest
from tests.storage import settings
from tests.unit.repository.clickhouse.test_transit import head, stop

from app.domain.errors import DataUnavailable
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.transit import ClickHouseTransitCatalog


def test_unpublished_rows_remain_hidden_then_snapshot_roundtrips() -> None:
    config = settings()
    reader = ClickHouseReader(config.clickhouse_url, config.clickhouse_user, config.clickhouse_password)
    database = 'test_transit_' + uuid4().hex

    def command(sql: str) -> None:
        with urlopen(Request(reader.url + '/', data=sql.encode(), headers=reader.headers), timeout=60) as response:
            response.read()

    command(f'CREATE DATABASE {database}')
    try:
        for table in ['snapshots', 'stops', 'connections']:
            command(f'CREATE TABLE {database}.{table} AS plexus_transit.{table}')
        station = {**stop(), 'snapshot': 'published'}
        command(f'INSERT INTO {database}.stops FORMAT JSONEachRow\n' + json.dumps(station))
        catalog = ClickHouseTransitCatalog(reader, database)
        with pytest.raises(DataUnavailable, match='published'):
            catalog.latest()
        published = {**head(), 'published_at': '2026-11-13T00:00:00+00:00'}
        command(f'INSERT INTO {database}.snapshots FORMAT JSONEachRow\n' + json.dumps(published))
        result = catalog.latest()
        assert result.id == 'published'
        assert result.stops[0].latitude is None
        assert result.clock_basis == 'source_clock' and result.timezone_verified is False
        assert result.connections == []
    finally:
        command(f'DROP DATABASE {database} SYNC')
