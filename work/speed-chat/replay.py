import json
import os
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
from typing import cast
from urllib.request import urlopen

from pydantic_ai import RunContext

from app.adapter.chat.artifacts import ChatRun
from app.adapter.chat.road_tools import RoadTools
from app.adapter.road_graph.data import GraphData
from app.adapter.road_graph.selection_geometry import selection_geometry
from app.domain.transport import NetworkMode, Season
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.graph_snapshot import ClickHouseGraphSnapshot
from app.repository.clickhouse.state import ClickHouseRoadJobStore
from app.usecase.chat import ChatContext
from app.usecase.road_geometry import RoadGeometry
from app.usecase.road_graph import RoadGraph, RoadJob


class ExistingRoads:
    def __init__(self) -> None:
        reader = ClickHouseReader(os.environ['CLICKHOUSE_URL'], os.environ['CLICKHOUSE_USER'],
                                  os.environ['CLICKHOUSE_PASSWORD'])
        self.data = GraphData(Path('data'), ClickHouseGraphSnapshot(reader))
        self.jobs = ClickHouseRoadJobStore(reader).load()

    def job(self, job_id: str) -> RoadJob:
        return self.jobs[job_id]

    def geometry(self, way_ids: list[int]) -> RoadGeometry:
        return selection_geometry(self.data, way_ids)


job_id = 'b217c537e87d4f02972134ee36b435a4'
roads = ExistingRoads()
run = ChatRun(ChatContext('94000000', Season.SUMMER, NetworkMode.ROAD, 'hansen'))
ctx = cast(RunContext[ChatRun], SimpleNamespace(deps=run))
RoadTools(cast(RoadGraph, roads)).road_calculation_status(ctx, job_id)
assert len(run.pending) == 1
with urlopen('http://127.0.0.1:8001/api/v1/road-scenarios/' + job_id) as response:
    job = json.load(response)
calculation = run.pending[0].calculation
assert calculation is not None
assert len(calculation.changes) == 39
assert {c.speed_factor for c in calculation.changes} == {1.2}
output = {'graph_revision': roads.data.revision, 'job': job, 'calculation': asdict(calculation)}
Path('work/speed-chat/acceptance.json').write_text(json.dumps(output, ensure_ascii=False, indent=2))
print(json.dumps({'status': job['status'], 'ways': len(calculation.changes),
                  'lines': len(calculation.corridor.lines), 'result': job['result']}, ensure_ascii=False))
