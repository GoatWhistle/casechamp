import json
from pathlib import Path
import osmium

class Roads(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.features = []

    def way(self, way):
        if way.tags.get('highway') not in ('trunk', 'primary', 'secondary'):
            return
        points = [[node.lon, node.lat] for node in way.nodes if node.location.valid()]
        if len(points) < 2 or not any(41.8 < p[0] < 42.4 and 44.8 < p[1] < 45.2 for p in points):
            return
        self.features.append({'type': 'Feature', 'properties': {'id': way.id, 'name': way.tags.get('name', way.tags.get('ref', 'Дорога'))}, 'geometry': {'type': 'LineString', 'coordinates': points}})

roads = Roads()
roads.apply_file('data/additional/stavropol/raw/north-caucasus-261107.osm.pbf', locations=True, idx='flex_mem')
Path('presentation/municipal-demo/roads.json').write_text(json.dumps({'type': 'FeatureCollection', 'features': roads.features}, ensure_ascii=False))
print(len(roads.features))
