import json
import os
from dataclasses import asdict
from pathlib import Path
from time import monotonic

from scipy.sparse.csgraph import dijkstra

from app.adapter.road_corridor.resolver import CorridorResolver
from app.adapter.road_graph.jobs import RoadJobs
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.graph_snapshot import ClickHouseGraphSnapshot
from app.repository.clickhouse.state import ClickHouseRoadJobStore
from app.settings import load_settings

config = load_settings(os.environ)
reader = ClickHouseReader(config.clickhouse_url, config.clickhouse_user, config.clickhouse_password)
roads = RoadJobs(Path('data'), ClickHouseGraphSnapshot(reader), ClickHouseRoadJobStore(reader))
resolver = CorridorResolver(roads)
start = monotonic()
route = resolver.resolve_route('Ставрополь, Ставропольский край', 'Александровское, Ставропольский край')
elapsed = monotonic() - start
corridor = route.corridor
points = roads.data.read('route_points', {'points': [
    str(roads.data.read('corridor_places', {'query': query})[0][0])
    for query in ('Ставрополь, Ставропольский край', 'Александровское, Ставропольский край')
]})
assert len(points) == 2
source = next(int(row[1]) for row in points if int(row[1]) >= 0)
node_set = [int(row[1]) for row in points]
expected = float(dijkstra(roads.delta.base.graph, directed=True, indices=node_set[0])[node_set[1]])
expected += sum(float(row[2] or 0) for row in points) / 15
assert abs(expected - route.travel_hours) < 1e-7
assert corridor.way_ids and corridor.regions
result = {
    'origin': corridor.origin, 'destination': corridor.destination,
    'way_count': len(corridor.way_ids), 'references': corridor.road_ref,
    'whole_way_km': corridor.length_km, 'travel_hours': route.travel_hours,
    'attachments_km': [corridor.origin_attachment_km, corridor.destination_attachment_km],
    'regions': [asdict(r) for r in corridor.regions], 'elapsed_seconds': elapsed,
    'independent_scipy_hours': expected, 'routing_method': route.routing_method,
    'graph': asdict(roads.metadata), 'scope': corridor.scope,
    'lines': corridor.lines,
}
Path('work/road-route/validation.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
print(json.dumps({k: v for k, v in result.items() if k != 'lines'}, ensure_ascii=False, indent=2))
roads.close()
