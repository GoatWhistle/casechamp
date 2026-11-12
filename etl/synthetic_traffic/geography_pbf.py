import hashlib
import json
import os
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path

from shapely import from_wkb, make_valid
from shapely.geometry import shape
from synthetic_traffic.geography_pbf_storage import query_vector_cache, read_manifest

__all__ = ["build_vector_cache", "query_vector_cache"]

try:
    import osmium
except ImportError:
    osmium = None


def _layers(tags):
    result = []
    if tags.get("building") not in (None, "no"):
        result.append("buildings")
    if (
        tags.get("boundary") == "protected_area"
        or tags.get("leisure") == "nature_reserve"
    ):
        result.append("protected")
    if (
        tags.get("natural") == "water"
        or tags.get("landuse") == "reservoir"
        or tags.get("waterway") == "riverbank"
    ):
        result.append("water")
    return result


class VectorHandler(osmium.SimpleHandler if osmium is not None else object):
    def __init__(self, connection):
        super().__init__()
        self.connection = connection
        self.factory = osmium.geom.WKBFactory()
        self.repairs = 0
        self.pending = set()
        self.early_areas = set()
        self.parse_failures = []
        self.counts = {key: 0 for key in ("buildings", "water", "protected")}

    def expect(self, kind, element):
        for layer in _layers(dict(element.tags)):
            key = layer, kind, element.id
            if key in self.early_areas:
                self.early_areas.remove(key)
            else:
                self.pending.add(key)

    def way(self, way):
        tags = dict(way.tags)
        if way.is_closed():
            self.expect("way", way)
        if tags.get("waterway") and tags.get("waterway") != "riverbank":
            geometry = from_wkb(bytes.fromhex(self.factory.create_linestring(way)))
            self.store("water", "way_line", way.id, geometry, "waterway_centerline")

    def relation(self, relation):
        if relation.tags.get("type") in {"multipolygon", "boundary"}:
            self.expect("relation", relation)

    def area(self, area):
        layers = _layers(dict(area.tags))
        if not layers:
            return
        kind = "way" if area.from_way() else "relation"
        try:
            geometry = from_wkb(bytes.fromhex(self.factory.create_multipolygon(area)))
            if not geometry.is_valid:
                geometry = make_valid(geometry)
                self.repairs += 1
            if (
                geometry.geom_type not in {"Polygon", "MultiPolygon"}
                or geometry.is_empty
            ):
                raise ValueError("Area is not a complete polygon")
        except (RuntimeError, ValueError) as error:
            self.parse_failures.append(
                {"kind": kind, "osm_id": area.orig_id(), "error": str(error)}
            )
            self.pending.update((layer, kind, area.orig_id()) for layer in layers)
            return
        for layer in layers:
            self.store(layer, kind, area.orig_id(), geometry, "assembled_osm_area")
            key = layer, kind, area.orig_id()
            if key in self.pending:
                self.pending.remove(key)
            else:
                self.early_areas.add(key)

    def store(self, layer, kind, osm_id, geometry, basis):
        if geometry.is_empty or not geometry.is_valid:
            raise ValueError(f"Invalid OSM geometry {kind}/{osm_id}")
        cursor = self.connection.execute(
            "INSERT INTO features(layer,kind,osm_id,basis,wkb) VALUES (?,?,?,?,?)",
            (layer, kind, osm_id, basis, geometry.wkb),
        )
        west, south, east, north = geometry.bounds
        self.connection.execute(
            "INSERT INTO spatial VALUES (?,?,?,?,?)",
            (cursor.lastrowid, west, east, south, north),
        )
        self.counts[layer] += 1


def build_vector_cache(pbf, sqlitepath, coverage=None):
    if osmium is None:
        raise RuntimeError("Building an OSM vector cache requires osmium>=4")
    if coverage is not None:
        geometry = shape(coverage)
        if (
            geometry.geom_type not in {"Polygon", "MultiPolygon"}
            or not geometry.is_valid
            or geometry.is_empty
        ):
            raise ValueError("Source coverage must be a valid sourced polygon")
    pbf, target = Path(pbf), Path(sqlitepath)
    digest = hashlib.sha256()
    with pbf.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    sha256 = digest.hexdigest()
    if target.exists():
        with sqlite3.connect(f"file:{target}?mode=ro", uri=True) as connection:
            manifest = read_manifest(connection)
        if manifest["pbf_sha256"] != sha256:
            raise ValueError(
                "Existing vector cache belongs to another PBF; use another output path"
            )
        return manifest
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + f".{uuid.uuid4().hex}.building")
    connection = sqlite3.connect(temporary)
    try:
        connection.executescript(
            "CREATE TABLE features (id INTEGER PRIMARY KEY, layer TEXT NOT NULL, kind TEXT NOT NULL, osm_id INTEGER NOT NULL, basis TEXT NOT NULL, wkb BLOB NOT NULL); CREATE VIRTUAL TABLE spatial USING rtree(id,min_lon,max_lon,min_lat,max_lat); CREATE TABLE expected(layer TEXT,kind TEXT,osm_id INTEGER,assembled INTEGER,PRIMARY KEY(layer,kind,osm_id)); CREATE TABLE metadata(key TEXT PRIMARY KEY,value TEXT NOT NULL);"
        )
        reader = osmium.io.Reader(str(pbf))
        header = reader.header()
        timestamp = header.get("osmosis_replication_timestamp") or None
        bounds = header.box()
        source_bounds = (
            [
                [
                    bounds.bottom_left.lon,
                    bounds.bottom_left.lat,
                    bounds.top_right.lon,
                    bounds.top_right.lat,
                ]
            ]
            if bounds.valid()
            else []
        )
        reader.close()
        handler = VectorHandler(connection)
        handler.apply_file(str(pbf), locations=True, idx="flex_mem")
        missing = sorted(handler.pending)
        connection.executemany(
            "INSERT OR REPLACE INTO expected VALUES (?,?,?,0)", missing
        )
        manifest = {
            "status": "incomplete" if missing else "complete",
            "format": "osm-vector-rtree-v1",
            "missing_areas": [
                {"layer": layer, "kind": kind, "osm_id": osm_id}
                for layer, kind, osm_id in missing
            ],
            "created_at": datetime.now(UTC).isoformat(),
            "pbf_path": str(pbf.resolve()),
            "pbf_sha256": sha256,
            "pbf_bytes": pbf.stat().st_size,
            "osm_timestamp": timestamp,
            "source_bounds": source_bounds,
            "coverage_geometry": coverage,
            "features": handler.counts,
            "geometry_repairs": handler.repairs,
            "deferred_geometry_failures": handler.parse_failures,
            "limits": [
                "Mapped OSM features only; absence is not surveyed clearance",
                "Waterway centerlines are not measured channel banks",
                "make_valid repairs are counted",
                "Full source area assembly required before publication",
            ],
        }
        connection.execute(
            "INSERT INTO metadata VALUES ('manifest',?)", (json.dumps(manifest),)
        )
        connection.execute("DELETE FROM expected WHERE assembled=1")
        connection.execute("CREATE INDEX feature_layer ON features(layer)")
        connection.commit()
        if connection.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            raise ValueError("Vector cache failed SQLite integrity check")
        connection.close()
        if missing:
            incomplete = target.with_name(target.name + ".incomplete")
            os.replace(temporary, incomplete)
            target.with_name(target.name + ".gaps.json").write_text(
                json.dumps(manifest, indent=2)
            )
            raise ValueError(
                f"OSM area assembly incomplete: {len(missing)} tagged source areas; cache retained at {incomplete}"
            )
        os.replace(temporary, target)
        return manifest
    except BaseException:
        connection.close()
        temporary.unlink(missing_ok=True)
        temporary.with_name(temporary.name + "-journal").unlink(missing_ok=True)
        raise
