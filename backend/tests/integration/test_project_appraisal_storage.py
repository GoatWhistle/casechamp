from urllib.request import Request, urlopen
from uuid import uuid4

from tests.storage import settings
from tests.unit.domain.test_project_appraisal import evidence, project

from app.domain.appraisal import appraise
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.records import columns, decode
from app.repository.clickhouse.state import ClickHouseRoadJobStore
from app.usecase.road_graph import RoadJob


def test_project_assumptions_and_results_roundtrip_in_real_storage() -> None:
    config = settings()
    reader = ClickHouseReader(
        config.clickhouse_url, config.clickhouse_user, config.clickhouse_password
    )
    store = ClickHouseRoadJobStore(reader)
    job = RoadJob(
        uuid4().hex,
        "18000000",
        "Volgograd",
        "road",
        [],
        "completed",
        5,
        5,
        "test-appraisal",
        appraisal_assumptions=project(),
        appraisal_result=appraise(project(), evidence()),
    )
    try:
        store.save(job)
        rows = reader.rows(
            "SELECT "
            + columns(RoadJob)
            + " FROM plexus_state.road_jobs FINAL WHERE id={id:String}",
            {"id": job.id},
        )
        restored: RoadJob = decode(RoadJob, rows[0])
        assert restored == job
    finally:
        request = Request(
            reader.url,
            data=(
                "ALTER TABLE plexus_state.road_jobs DELETE WHERE id='"
                + job.id
                + "' SETTINGS mutations_sync=1"
            ).encode(),
            headers=reader.headers,
        )
        with urlopen(request, timeout=30) as response:
            response.read()
