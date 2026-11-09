import json
import math
import sys
from collections import defaultdict
from pathlib import Path

import duckdb
import osmium

CELL = 0.1
con = duckdb.connect()
rows = con.execute("""
select p.point_id, p.region, p.population, p.snap_km, p.lon, p.lat,
       n.lon, n.lat
from 'data/graph_ru/points.parquet' p
join 'data/graph_ru/nodes.parquet' n using(node)
where p.on_road and p.snap_km > 1
""").fetchall()

def cells(a, b):
    for x in range(math.floor(min(a[0], b[0]) / CELL), math.floor(max(a[0], b[0]) / CELL) + 1):
        for y in range(math.floor(min(a[1], b[1]) / CELL), math.floor(max(a[1], b[1]) / CELL) + 1):
            yield x, y

def cross(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

def proper_intersection(a, b, c, d):
    return cross(a, b, c) * cross(a, b, d) < 0 and cross(c, d, a) * cross(c, d, b) < 0

segments = []
grid = defaultdict(list)
for point_id, region, population, snap_km, lon, lat, target_lon, target_lat in rows:
    a, b = (lon, lat), (target_lon, target_lat)
    i = len(segments)
    segments.append((point_id, region, population, snap_km, a, b))
    for cell in cells(a, b):
        grid[cell].append(i)

class Water(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.found = defaultdict(dict)
        self.ways = 0

    def way(self, way):
        kind = way.tags.get('waterway')
        if kind not in {'river', 'stream', 'canal', 'drain', 'ditch'}:
            return
        self.ways += 1
        previous = None
        for node in way.nodes:
            current = (node.lon, node.lat) if node.location.valid() else None
            if previous is not None and current is not None:
                candidates = set()
                for cell in cells(previous, current):
                    candidates.update(grid.get(cell, ()))
                for i in candidates:
                    point_id, region, population, snap_km, a, b = segments[i]
                    if proper_intersection(a, b, previous, current):
                        self.found[point_id][way.id] = {'id': way.id, 'waterway': kind, 'name': way.tags.get('name'), 'tunnel': way.tags.get('tunnel'), 'intermittent': way.tags.get('intermittent')}
            previous = current

label = sys.argv[1]
handler = Water()
handler.apply_file(str(Path('data/raw/osm_russia') / f'{label}.osm.pbf'), locations=True, idx='flex_mem')
results = []
for point_id, region, population, snap_km, a, b in segments:
    if point_id in handler.found:
        results.append({'point_id': point_id, 'region': region, 'population': population, 'snap_km': snap_km, 'start_lon_lat': a, 'anchor_lon_lat': b, 'ways': list(handler.found[point_id].values())})
results.sort(key=lambda x: (-x['population'], x['point_id']))
print(json.dumps({'source': f'{label}.osm.pbf', 'candidate_segments': len(segments), 'water_ways_processed': handler.ways, 'matches': results, 'scope': 'strict crossings of linear OSM waterway ways only; no denominator for PBF coverage, no confirmation of barriers or navigability'}, ensure_ascii=False, indent=2))
