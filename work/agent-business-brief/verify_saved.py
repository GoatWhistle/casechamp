import json
import os
from dataclasses import asdict
from pathlib import Path

from app.adapter.chat.stress_tools import StressTools
from app.adapter.road_corridor.resolver import CorridorResolver
from app.adapter.road_graph.jobs import RoadJobs
from app.adapter.road_graph.selection_geometry import SelectionGeometry
from app.adapter.road_stress.jobs import StressJobs
from app.repository.clickhouse.atlas import ClickHouseAtlasRepository
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.graph_snapshot import ClickHouseGraphSnapshot
from app.repository.clickhouse.state import ClickHouseRoadJobStore
from app.repository.clickhouse.stress import ClickHouseStressStore
from app.settings import load_settings
from app.usecase.calculation_tables import CalculationTables
from app.usecase.chat_calculation_review import CalculationReview, CalculationReviews
from app.usecase.road_corridor import RoadCorridors
from app.usecase.road_graph import RoadGraph

config = load_settings(os.environ)
reader = ClickHouseReader(config.clickhouse_url, config.clickhouse_user, config.clickhouse_password)
engine = RoadJobs(config.graph_dir, ClickHouseGraphSnapshot(reader), ClickHouseRoadJobStore(reader), 6)
try:
    roads = RoadGraph(engine, ClickHouseAtlasRepository(reader), geometry_source=SelectionGeometry(engine.data))
    stress = StressJobs(engine, ClickHouseStressStore(reader))
    corridors = RoadCorridors(CorridorResolver(engine))
    completed = [job for job in stress.recent() if job.status == "completed" and job.version == engine.data.version]
    matching = [(job, roads.closure_jobs(job.way_ids, job.version)) for job in completed]
    job, indices = next(((j, rows) for j, rows in matching if any(r.status == "completed" for r in rows)), matching[0])
    table_jobs = [j.id for j, rows in matching if rows and all(r.status == "completed" for r in rows)][:2]
    tables = CalculationTables(roads, stress).build([], table_jobs)
    Path('work/agent-business-brief/comparison-tables.json').write_text(json.dumps([asdict(table) for table in tables], ensure_ascii=False, indent=2))
    region = indices[0].region if indices else job.regions[0].name
    evidence = json.loads(StressTools(stress, corridors, roads).reply(job.id, region, 0))
    Path('work/agent-business-brief/live-evidence.json').write_text(json.dumps(evidence, ensure_ascii=False, indent=2))
    print(json.dumps({"stress_id": job.id, "region": region, "indices": [{"region": row.region, "status": row.status, "result": asdict(row.result) | {"settlement_effects": []} if row.result else None} for row in indices], "consequences": evidence["summary"]["consequences"] is not None, "traffic_scenarios": len(evidence["traffic"]), "region_count": len(evidence["region_overview"])}, ensure_ascii=False))
    if indices and all(row.status in {"completed", "failed", "cancelled"} for row in indices):
        prompt = CalculationReviews(roads, stress, corridors).prompt(CalculationReview(stress_ids=(job.id,)))
        Path('work/agent-business-brief/review-payload.txt').write_text(prompt)
        print('Combined review payload verified')
finally:
    engine.close()
