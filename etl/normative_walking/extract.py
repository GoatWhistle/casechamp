import json
from collections import Counter
from pathlib import Path

import osmium
import pyarrow as pa
import pyarrow.parquet as pq

from app.domain.normative.walking import (
    blocked_node,
    metres_between,
    residential,
    walkable,
    walking_directions,
)


class RowWriter:
    def __init__(self, path: Path, schema: pa.Schema) -> None:
        self.writer = pq.ParquetWriter(path, schema)
        self.schema = schema
        self.rows = []
        self.count = 0

    def append(self, row: dict) -> None:
        self.rows.append(row)
        self.count += 1
        if len(self.rows) >= 20000:
            self.flush()

    def flush(self) -> None:
        if self.rows:
            self.writer.write_table(pa.Table.from_pylist(self.rows, schema=self.schema))
            self.rows.clear()

    def close(self) -> None:
        self.flush()
        self.writer.close()


class Extractor(osmium.SimpleHandler):
    def __init__(self, folder: Path, revision: str) -> None:
        super().__init__()
        self.revision = revision
        self.blocked = set()
        self.indices = {}
        self.coordinates = []
        self.counts = Counter()
        self.edges = RowWriter(folder / "edges.parquet", pa.schema([
            ("revision", pa.string()), ("way_id", pa.int64()),
            ("source", pa.uint32()), ("target", pa.uint32()), ("metres", pa.float64()),
        ]))
        self.origins = RowWriter(folder / "origins.parquet", pa.schema([
            ("revision", pa.string()), ("id", pa.string()), ("name", pa.string()),
            ("latitude", pa.float64()), ("longitude", pa.float64()),
            ("coordinate_source", pa.string()), ("origin_type", pa.string()),
        ]))

    def node(self, obj) -> None:
        if blocked_node(dict(obj.tags)):
            self.blocked.add(obj.id)

    def index(self, node) -> int:
        if node.ref not in self.indices:
            self.indices[node.ref] = len(self.coordinates)
            self.coordinates.append((node.ref, node.lat, node.lon))
        return self.indices[node.ref]

    def way(self, obj) -> None:
        tags = dict(obj.tags)
        if residential(tags):
            self.origin(obj, tags)
        if not tags.get("highway"):
            return
        if not walkable(tags):
            self.counts["excluded_way"] += 1
            return
        if any(not node.location.valid() for node in obj.nodes):
            self.counts["missing_geometry"] += 1
            return
        forward, backward = walking_directions(tags)
        for first, second in zip(obj.nodes, list(obj.nodes)[1:]):
            if first.ref in self.blocked or second.ref in self.blocked:
                self.counts["blocked_segment"] += 1
                continue
            distance = metres_between((first.lon, first.lat), (second.lon, second.lat))
            if distance <= 0:
                self.counts["zero_segment"] += 1
                continue
            a, b = self.index(first), self.index(second)
            directions = ([(a, b)] if forward else []) + ([(b, a)] if backward else [])
            for source, target in directions:
                self.edges.append({"revision": self.revision, "way_id": obj.id,
                                   "source": source, "target": target, "metres": distance})
        self.counts["walkable_way"] += 1

    def origin(self, obj, tags: dict) -> None:
        if not obj.is_closed() or any(not node.location.valid() for node in obj.nodes):
            self.counts["missing_building_geometry"] += 1
            return
        points = [(node.lon, node.lat) for node in obj.nodes][:-1]
        if not points:
            return
        address = ", ".join(filter(None, [tags.get("addr:city"), tags.get("addr:street"),
                                          tags.get("addr:housenumber")]))
        self.origins.append({
            "revision": self.revision, "id": f"osm-way-{obj.id}",
            "name": address or f"OSM way {obj.id}",
            "latitude": sum(point[1] for point in points) / len(points),
            "longitude": sum(point[0] for point in points) / len(points),
            "coordinate_source": f"https://www.openstreetmap.org/way/{obj.id}",
            "origin_type": "residential_building_reference",
        })

    def finish(self, folder: Path) -> dict:
        self.edges.close()
        self.origins.close()
        schema = pa.schema([("revision", pa.string()), ("node_index", pa.uint32()),
                            ("osm_id", pa.int64()), ("latitude", pa.float64()),
                            ("longitude", pa.float64())])
        writer = RowWriter(folder / "nodes.parquet", schema)
        for index, (osm_id, lat, lon) in enumerate(self.coordinates):
            writer.append({"revision": self.revision, "node_index": index,
                           "osm_id": osm_id, "latitude": lat, "longitude": lon})
        writer.close()
        counts = {**self.counts, "nodes": writer.count, "edges": self.edges.count,
                  "residential_buildings": self.origins.count, "blocked_nodes": len(self.blocked)}
        (folder / "counts.json").write_text(json.dumps(counts, indent=2) + "\n")
        return counts
