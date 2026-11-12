import fcntl
import hashlib
import json
import os
import sqlite3
from pathlib import Path
from urllib.parse import urlencode
from uuid import uuid4

import rasterio
from shapely.geometry import box, mapping, shape
from synthetic_traffic.geography_fetch import OVERPASS, dem_url, download, osm_geometry
from synthetic_traffic.geography_pbf import query_vector_cache

CACHE_LIMIT = 2_000_000_000


def _hash(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as source:
        for chunk in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _trim(cache, limit, keep=None):
    entries = sorted(cache.glob("*.tif"), key=lambda path: path.stat().st_mtime)
    total = sum(path.stat().st_size for path in entries)
    for path in entries:
        if total <= limit:
            break
        if path == keep:
            continue
        total -= path.stat().st_size
        path.unlink(missing_ok=True)
        path.with_suffix(".json").unlink(missing_ok=True)


def _dem(lat, lon, cache):
    cache.mkdir(parents=True, exist_ok=True)
    url = dem_url(lat, lon)
    tile = cache / (hashlib.sha256(url.encode()).hexdigest() + ".tif")
    with tile.with_suffix(".lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        record = tile.with_suffix(".json")
        if tile.is_file() and not record.is_file():
            tile.unlink()
        if tile.is_file() and record.is_file():
            metadata = json.loads(record.read_text())
            if metadata.get("sha256") != _hash(tile):
                tile.unlink()
        if not tile.is_file():
            _trim(cache, CACHE_LIMIT - 100_000_000)
            temporary = tile.with_name(tile.name + "." + uuid4().hex + ".tmp")
            try:
                metadata = download(url, temporary)
                with rasterio.open(temporary) as dataset:
                    if dataset.count != 1 or dataset.crs is None:
                        raise ValueError(
                            "DEM tile has no single georeferenced elevation band"
                        )
                temporary.replace(tile)
                record.write_text(json.dumps(metadata))
            finally:
                temporary.unlink(missing_ok=True)
        os.utime(tile)
        _trim(cache, CACHE_LIMIT, keep=tile)
        return tile, json.loads(record.read_text())


def _vectors(bbox, resolution, temporary, vector_cache):
    fallback_reason = None
    if vector_cache is not None:
        source = Path(vector_cache)
        with sqlite3.connect(
            source.resolve().as_uri() + "?mode=ro", uri=True
        ) as connection:
            row = connection.execute(
                "SELECT value FROM metadata WHERE key='manifest'"
            ).fetchone()
        provenance = json.loads(row[0]) if row else {}
        coverage = provenance.get("coverage_geometry")
        geometry = shape(coverage) if coverage else None
        if geometry is None or not geometry.is_valid or not geometry.covers(box(*bbox)):
            fallback_reason = (
                "extract_coverage_polygon_unknown_or_does_not_cover_entire_tile"
            )
        else:
            try:
                values = query_vector_cache(source, bbox, resolution=resolution)
            except ValueError as error:
                if (
                    "cover" not in str(error).lower()
                    and "outside" not in str(error).lower()
                ):
                    raise
                fallback_reason = str(error)
            else:
                return values, {
                    "source_manifest": provenance,
                    "provider": "OpenStreetMap PBF vector cache",
                    "path": str(source.resolve()),
                    "bytes": source.stat().st_size,
                    "acquired_from": "completed_source_cache",
                    "coverage_check": "exact_extract_polygon_covers_entire_tile",
                }
    west, south, east, north = bbox
    bounds = f"({south},{west},{north},{east})"
    selectors = [
        "[building]",
        "[natural=water]",
        "[waterway]",
        "[landuse=reservoir]",
        "[boundary=protected_area]",
        "[leisure=nature_reserve]",
    ]
    query = (
        "[out:json][timeout:90];("
        + "".join(f"nwr{selector}{bounds};" for selector in selectors)
        + ");out geom;"
    )
    record = download(
        OVERPASS, temporary / "osm.json", urlencode({"data": query}).encode()
    )
    document = json.loads((temporary / "osm.json").read_text())
    if document.get("remark"):
        raise ValueError(f"Overpass did not complete: {document['remark']}")
    values = {key: [] for key in ("water", "buildings", "protected")}
    for element in document.get("elements", []):
        if element["type"] == "node":
            continue
        tags = element.get("tags", {})
        layer = (
            "buildings"
            if "building" in tags
            else "protected"
            if tags.get("boundary") == "protected_area"
            or tags.get("leisure") == "nature_reserve"
            else "water"
        )
        values[layer].append(
            {
                "type": "Feature",
                "geometry": mapping(osm_geometry(element, resolution)),
                "properties": {"osm_id": element["id"], "osm_type": element["type"]},
            }
        )
    if fallback_reason:
        record = {**record, "vector_cache_fallback": fallback_reason}
    return values, record
