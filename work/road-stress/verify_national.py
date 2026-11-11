import json
import os
from dataclasses import asdict
from pathlib import Path
from time import monotonic, sleep

from app.adapter.road_graph.jobs import RoadJobs
from app.adapter.road_stress.jobs import StressJobs
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.graph_snapshot import ClickHouseGraphSnapshot
from app.repository.clickhouse.state import ClickHouseRoadJobStore
from app.repository.clickhouse.stress import ClickHouseStressStore
from app.settings import load_settings

def main() -> None:
    config = load_settings(os.environ)
    reader = ClickHouseReader(config.clickhouse_url, config.clickhouse_user, config.clickhouse_password)
    roads = RoadJobs(Path("data"), ClickHouseGraphSnapshot(reader), ClickHouseRoadJobStore(reader), 6)
    stress = StressJobs(roads, ClickHouseStressStore(reader))
    ways = roads.data.read("references", {"references": ["М-10"]})
    if not ways:
        raise RuntimeError("Reference road unavailable")
    started = monotonic()
    job = stress.submit([int(ways[0][1])])
    print("Job", job.id, flush=True)
    last = None
    while job.status in {"queued", "running"}:
        sleep(2)
        job = stress.get(job.id)
        state = job.stage, job.completed
        if state != last:
            print(state, flush=True)
            last = state
    result = {"job": asdict(job), "elapsed_seconds": monotonic() - started}
    Path("work/road-stress/national-validation.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
    roads.close()
    if job.status != "completed":
        raise RuntimeError(job.error or job.status)
    print("Completed", result["elapsed_seconds"], flush=True)


if __name__ == "__main__":
    main()
