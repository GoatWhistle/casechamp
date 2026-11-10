import json
import os
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace
from typing import cast
from urllib.request import Request, urlopen

from pydantic_ai import RunContext

from app.adapter.chat.artifacts import ChatRun
from app.adapter.chat.bridge_tools import BridgeTools
from app.adapter.road_corridor.resolver import CorridorResolver
from app.adapter.road_graph.data import GraphData
from app.adapter.road_graph.jobs import RoadJobs
from app.domain.transport import NetworkMode, Season
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.graph_snapshot import ClickHouseGraphSnapshot
from app.usecase.chat import ChatContext
from app.usecase.road_corridor import RoadCorridors
from app.usecase.road_graph import RoadChange, RoadJob


class LocalApiRoads:
    def __init__(self) -> None:
        reader = ClickHouseReader(
            os.environ["CLICKHOUSE_URL"], os.environ["CLICKHOUSE_USER"],
            os.environ["CLICKHOUSE_PASSWORD"],
        )
        self.data = GraphData(Path("data"), ClickHouseGraphSnapshot(reader))

    def submit(
        self, region_id: str, region: str, scenario: str,
        changes: list[RoadChange], *, queue: bool = False,
    ) -> RoadJob:
        request = Request(
            "http://127.0.0.1:8001/api/v1/road-scenarios",
            data=json.dumps({
                "region_id": region_id, "scenario": scenario,
                "changes": [asdict(c) for c in changes],
            }).encode(),
            headers={"Content-Type": "application/json"},
        )
        with urlopen(request, timeout=30) as response:
            result = json.load(response)
        result["changes"] = [RoadChange(**row) for row in result["changes"]]
        return RoadJob(**result)


roads = LocalApiRoads()
tools = BridgeTools(RoadCorridors(CorridorResolver(cast(RoadJobs, roads))))
run = ChatRun(ChatContext("63000000", Season.SUMMER, NetworkMode.ROAD, "hansen"))
ctx = cast(RunContext[ChatRun], SimpleNamespace(deps=run))
direct = json.loads(tools.find_road_bridges(ctx, "Саратов", 10, "Саратовский мост"))
bypass = json.loads(tools.find_road_bridges(ctx, "Пристанное, Саратовская область", 2))
selected = direct["candidates"] + [
    c for c in bypass["candidates"] if c["road_references"] == ["А-298"]
]
assert len(selected) == 2
assert sorted(w for c in selected for w in c["way_ids"]) == [27262951, 122013785, 203336910]
result = json.loads(tools.close_road_bridges(ctx, [c["bridge_id"] for c in selected]))
assert result["status"] == "submitted", result
assert len(result["jobs"]) == 1
output = {
    "graph_revision": roads.data.revision,
    "selected": selected, "submission": result,
    "calculation": asdict(run.pending[0].calculation),
}
Path("work/bridge-selection/acceptance.json").write_text(
    json.dumps(output, ensure_ascii=False, indent=2)
)
print(json.dumps(result, ensure_ascii=False))
