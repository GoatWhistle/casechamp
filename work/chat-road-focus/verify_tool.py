import json
import os
from dataclasses import asdict
from pathlib import Path
from types import SimpleNamespace

from app.adapter.chat.artifacts import ChatRun
from app.adapter.chat.atlas_requests import RoadPresentation
from app.adapter.chat.map_tools import MapTools
from app.adapter.road_graph.data import GraphData
from app.adapter.road_graph.selection_geometry import SelectionGeometry
from app.domain.transport import NetworkMode, Season
from app.repository.clickhouse.atlas import ClickHouseAtlasRepository
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.graph_snapshot import ClickHouseGraphSnapshot
from app.settings import load_settings
from app.usecase.chat import ChatContext
from app.usecase.regions import RegionQueries

config = load_settings(os.environ)
reader = ClickHouseReader(config.clickhouse_url, config.clickhouse_user, config.clickhouse_password)
atlas = ClickHouseAtlasRepository(reader)
geometry = SelectionGeometry(GraphData(Path('data'), ClickHouseGraphSnapshot(reader)))
tools = MapTools(RegionQueries(atlas), roads=geometry)
run = ChatRun(ChatContext(None, Season.SUMMER, NetworkMode.ROAD, 'hansen'))
reply = tools.present_atlas(SimpleNamespace(deps=run), RoadPresentation('road', [201616290]))
command = run.pending[0].map
assert command is not None and command.road is not None
assert .166 < command.road.length_km < .168
output = Path('work/chat-road-focus/real-command.json')
output.write_text(json.dumps(asdict(command), ensure_ascii=False, indent=2) + '\n')
print(reply)
print('stored_map_event', output)
