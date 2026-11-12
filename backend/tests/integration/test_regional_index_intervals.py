import json
from dataclasses import asdict
from urllib.request import Request, urlopen
from uuid import uuid4

from tests.storage import settings
from tests.unit.domain.normative.test_index import basis

from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.index_bases import ClickHouseIndexBasisRepository


def test_source_intervals_round_trip_without_choosing_a_single_cutoff() -> None:
    config = settings()
    reader = ClickHouseReader(
        config.clickhouse_url, config.clickhouse_user, config.clickhouse_password
    )
    repository = ClickHouseIndexBasisRepository(reader)
    repository.table = "plexus_normative.test_index_intervals_" + uuid4().hex

    def command(sql: str) -> None:
        request = Request(reader.url + "/", data=sql.encode(), headers=reader.headers)
        with urlopen(request, timeout=60) as response:
            response.read()

    command(f"CREATE TABLE {repository.table} AS plexus_normative.index_bases")
    try:
        intervals = [
            {
                "minimum": 30,
                "maximum": 40,
                "municipality_type": "urban_okrug",
                "mode": "transport",
                "profile": "municipal_library",
            }
        ]
        row = {
            **asdict(basis()),
            "region_id": "R",
            "criterion_id": "N07",
            "regulation": "local_selection_required",
            "required_mode": "none",
            "thresholds": [],
            "intervals": json.dumps(intervals),
            "review": "",
            "updated_at": "2026-11-12 12:00:00.000",
        }
        command(f"INSERT INTO {repository.table} FORMAT JSONEachRow\n" + json.dumps(row))
        saved = repository.basis("R", "N07")
        assert saved is not None
        assert saved.thresholds == ()
        assert saved.regulation == "local_selection_required"
        assert saved.intervals[0].minimum == 30
        assert saved.intervals[0].maximum == 40
        assert saved.intervals[0].municipality_type == "urban_okrug"
        assert repository.basis("Other", "N07") is None
    finally:
        command(f"DROP TABLE {repository.table}")
