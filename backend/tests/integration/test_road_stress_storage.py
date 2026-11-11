from urllib.request import Request, urlopen
from uuid import uuid4

from tests.storage import settings

from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.stress import ClickHouseStressStore
from app.usecase.road_stress import StressImpact, StressJob, StressPoint, StressTotals


def test_stress_results_roundtrip() -> None:
    config = settings()
    reader = ClickHouseReader(config.clickhouse_url, config.clickhouse_user, config.clickhouse_password)
    store = ClickHouseStressStore(reader)
    key = uuid4().hex
    job = StressJob(key, "test", [1, 2], status="completed")
    point = StressPoint("test-point", "Test", "Test region", 100, 1, 0, 30, 50)
    impact = StressImpact(point, 1, True, 0, "Market")
    try:
        store.save(job)
        store.save_impacts(key, [impact])
        store.save_baseline(key, 0, [1.0, float("inf"), 80.0])
        assert next(row for row in store.load() if row.id == key) == job
        assert store.impacts(key) == [impact]
        assert store.totals(key, "Test region") == StressTotals(1, 100, 1, 100, 0, 1)
        assert store.totals(key, "Missing region") == StressTotals(0, 0, 0, 0, 0, 0)
        second = StressPoint("second", "Second", "Other", 50, 2, 0, 31, 50)
        store.save_impacts(key, [impact, StressImpact(second, 0, False, 65, "Market")])
        assert store.totals(key) == StressTotals(2, 150, 1, 100, 65, 2)
        assert list(store.baseline(key)) == [(0, [1.0, float("inf"), 80.0])]
    finally:
        for table, column in (("stress_jobs", "id"), ("stress_impacts", "id"), ("stress_point_impacts", "job_id"), ("stress_baseline", "version")):
            request = Request(reader.url, data=(f"ALTER TABLE plexus_state.{table} DELETE WHERE {column}='{key}' SETTINGS mutations_sync=1").encode(), headers=reader.headers)
            with urlopen(request, timeout=30) as response:
                response.read()
