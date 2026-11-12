import hashlib
import json
import os
import shutil
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path

from shapely.geometry import mapping, shape
from shapely.ops import unary_union
from synthetic_traffic.geography_pbf_storage import read_manifest


def file_digest(path):
    with Path(path).open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()


def merge_vector_caches(sources, output):
    paths = [Path(source) for source in sources]
    if len(paths) < 2 or len({path.resolve() for path in paths}) != len(paths):
        raise ValueError("A vector union needs at least two distinct completed caches")
    records = []
    for path in paths:
        with sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True) as db:
            manifest = read_manifest(db)
        if not manifest.get("coverage_geometry"):
            raise ValueError("Every vector source needs exact coverage geometry")
        records.append(
            {
                "path": str(path.resolve()),
                "sha256": file_digest(path),
                "bytes": path.stat().st_size,
                "manifest": manifest,
            }
        )
    records.sort(
        key=lambda row: (row["manifest"].get("osm_timestamp") or "", row["sha256"])
    )
    geometries = [shape(row["manifest"]["coverage_geometry"]) for row in records]
    if any(not geometry.is_valid or geometry.is_empty for geometry in geometries):
        raise ValueError("Vector source coverage is invalid")
    output = Path(output)
    if output.exists():
        raise ValueError("Union output already exists; choose another path")
    output.parent.mkdir(parents=True, exist_ok=True)
    if shutil.disk_usage(output.parent).free < 15 * 1024**3:
        raise RuntimeError("Vector union paused because less than15GBdiskspace remains")
    if sum(row["bytes"] for row in records) > 30 * 1024**3:
        raise RuntimeError("Vector union source size exceeds30GBdatasetbudget")
    temporary = output.with_name(output.name + f".{uuid.uuid4().hex}.building")
    shutil.copyfile(records[0]["path"], temporary)
    db = sqlite3.connect(temporary, uri=True)
    try:
        db.execute("CREATE UNIQUE INDEX union_identity ON features(layer,kind,osm_id)")
        db.execute(
            "ALTER TABLE features ADD COLUMN source_cache INTEGER NOT NULL DEFAULT 0"
        )
        db.commit()
        for index, record in enumerate(records[1:], 1):
            db.execute(
                "ATTACH DATABASE ? AS incoming",
                (Path(record["path"]).as_uri() + "?mode=ro",),
            )
            db.execute(
                "INSERT INTO features(layer,kind,osm_id,basis,wkb,source_cache) SELECT layer,kind,osm_id,basis,wkb,? FROM incoming.features WHERE 1 ON CONFLICT(layer,kind,osm_id) DO UPDATE SET basis=excluded.basis,wkb=excluded.wkb,source_cache=excluded.source_cache WHERE features.basis!='official_osm_api_complete_area_repair' OR excluded.basis='official_osm_api_complete_area_repair'",
                (index,),
            )
            db.execute(
                "INSERT OR REPLACE INTO spatial SELECT destination.id,bounds.min_lon,bounds.max_lon,bounds.min_lat,bounds.max_lat FROM incoming.features source JOIN incoming.spatial bounds ON bounds.id=source.id JOIN features destination ON destination.layer=source.layer AND destination.kind=source.kind AND destination.osm_id=source.osm_id WHERE destination.source_cache=?",
                (index,),
            )
            db.commit()
            db.execute("DETACH DATABASE incoming")
        manifest = {
            "status": "complete",
            "format": "osm-vector-rtree-union-v1",
            "created_at": datetime.now(UTC).isoformat(),
            "coverage_geometry": mapping(unary_union(geometries)),
            "source_caches": records,
            "features": dict(
                db.execute("SELECT layer,count(*) FROM features GROUP BY layer")
            ),
            "source_precedence": "Newer PBF snapshot overrides older raw features; complete official OSM API repairs override raw PBF copies",
            "snapshot_basis": "union_of_source_snapshots_with_explicit_per_feature_source_cache",
            "limits": [
                "Mapped OSM features only; absence is not surveyed clearance",
                "Source timestamps differ and are retained in each source manifest",
                "Waterway centerlines are not measured channel banks",
            ],
        }
        db.execute(
            "UPDATE metadata SET value=? WHERE key='manifest'", (json.dumps(manifest),)
        )
        db.commit()
        if db.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            raise ValueError("Merged vector cache failed SQLite integrity check")
        db.close()
        if any(file_digest(record["path"]) != record["sha256"] for record in records):
            raise ValueError("Source vector cache changed during merge")
        os.replace(temporary, output)
        return manifest
    except BaseException:
        db.close()
        temporary.unlink(missing_ok=True)
        temporary.with_name(temporary.name + "-journal").unlink(missing_ok=True)
        raise
