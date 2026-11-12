from collections import Counter
from pathlib import Path

import pyarrow as pa

from app.domain.normative.walking import blocked_node, metres_between, residential, walkable, walking_directions
from extract_national_pois import RegionIndex
from normative_walking.extract import RowWriter
from normative_walking.regional_geometry import line_geometry

SCHEMAS = {
    'edges': pa.schema([('source', pa.int64()), ('target', pa.int64()), ('metres', pa.float64()), ('way_id', pa.int64())]),
    'nodes': pa.schema([('osm_id', pa.int64()), ('latitude', pa.float64()), ('longitude', pa.float64())]),
    'origins': pa.schema([('id', pa.string()), ('name', pa.string()), ('latitude', pa.float64()), ('longitude', pa.float64()), ('coordinate_source', pa.string()), ('origin_type', pa.string())]),
}


class RegionalRaw:
    def __init__(self, output: Path, regions: RegionIndex) -> None:
        self.output = output
        self.regions = regions
        self.blocked = set()
        self.writers = {}
        self.counts = Counter()

    def writer(self, region_id: str, kind: str) -> RowWriter:
        key = (region_id, kind)
        if key not in self.writers:
            folder = self.output / region_id
            folder.mkdir(parents=True, exist_ok=True)
            self.writers[key] = RowWriter(folder / (kind + '.parquet'), SCHEMAS[kind])
        return self.writers[key]

    def process(self, obj) -> None:
        tags = dict(obj.tags)
        if obj.is_node():
            if blocked_node(tags):
                self.blocked.add(obj.id)
            return
        if not obj.is_way():
            return
        is_home = residential(tags)
        is_path = walkable(tags)
        if not is_home and not is_path:
            return
        if any(not node.location.valid() for node in obj.nodes):
            self.counts['missing_geometry'] += 1
            return
        if is_home:
            self.origin(obj, tags)
        if not is_path or len(obj.nodes) < 2:
            return
        coordinates = [(node.lon, node.lat) for node in obj.nodes]
        hits = self.regions.tree.query(line_geometry(coordinates), predicate='intersects')
        forward, backward = walking_directions(tags)
        segments, used = [], {}
        for left, right in zip(obj.nodes, list(obj.nodes)[1:]):
            if left.ref in self.blocked or right.ref in self.blocked:
                self.counts['blocked_segment'] += 1
                continue
            distance = metres_between((left.lon, left.lat), (right.lon, right.lat))
            if distance <= 0:
                continue
            used[left.ref] = (left.lat, left.lon)
            used[right.ref] = (right.lat, right.lon)
            if forward:
                segments.append((left.ref, right.ref, distance))
            if backward:
                segments.append((right.ref, left.ref, distance))
        for hit in hits:
            region = self.regions.regions[int(hit)]['id']
            nodes, edges = self.writer(region, 'nodes'), self.writer(region, 'edges')
            for osm_id, (lat, lon) in used.items():
                nodes.append({'osm_id': osm_id, 'latitude': lat, 'longitude': lon})
            for source, target, metres in segments:
                edges.append({'source': source, 'target': target, 'metres': metres, 'way_id': obj.id})
        self.counts['walkable_ways'] += 1

    def origin(self, obj, tags: dict) -> None:
        if not obj.is_closed() or len(obj.nodes) < 4:
            return
        points = [(node.lon, node.lat) for node in obj.nodes][:-1]
        lat = sum(point[1] for point in points) / len(points)
        lon = sum(point[0] for point in points) / len(points)
        region, _, status = self.regions.locate(lat, lon)
        if status != 'spatial_match':
            self.counts['origin_' + status] += 1
            return
        address = ', '.join(tags[key] for key in ('addr:city', 'addr:street', 'addr:housenumber') if tags.get(key))
        self.writer(region, 'origins').append({'id': f'osm-way-{obj.id}', 'name': address or f'OSM way {obj.id}',
                                             'latitude': lat, 'longitude': lon, 'coordinate_source': f'https://www.openstreetmap.org/way/{obj.id}',
                                             'origin_type': 'residential_building_reference'})

    def finish(self) -> dict:
        result = {}
        for (region, kind), writer in self.writers.items():
            writer.close()
            result.setdefault(region, {})[kind] = writer.count
        return {'regions': result, 'counts': dict(self.counts), 'blocked_nodes': len(self.blocked)}
