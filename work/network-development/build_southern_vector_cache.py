import hashlib
import json
import os
import shutil
import sqlite3
import time
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError

from shapely.geometry import box, shape
from synthetic_traffic import geography_pbf
from synthetic_traffic.geography_fetch import download as download_object
from synthetic_traffic.geography_pbf_repair import repair_vector_cache
from synthetic_traffic.geography_pbf_union import merge_vector_caches

ROOT = Path("/private/tmp/plexus-geography/data/southern-fallback")
MAIN = Path("/Users/andreykuronskin/keys_champ/data/traffic-geography-national")
SOURCE = ROOT / "south-fed-district-261111.osm.pbf"
CACHE = ROOT / "south-vector-cache.sqlite"
STATE = ROOT / "state.json"


def state(phase, **details):
    value = {
        "phase": phase,
        "pid": os.getpid(),
        "updated_at": datetime.now(UTC).isoformat(),
        **details,
    }
    temporary = STATE.with_suffix(".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2))
    temporary.replace(STATE)
    print(json.dumps(value, ensure_ascii=False), flush=True)


class Progress(geography_pbf.VectorHandler):
    def store(self, *args):
        super().store(*args)
        count = sum(self.counts.values())
        if count % 100000 == 0:
            state("building", features=count, counts=self.counts)


def main():
    ROOT.mkdir(parents=True, exist_ok=True)
    while not SOURCE.exists():
        state("waiting_for_download")
        time.sleep(10)
    if shutil.disk_usage(ROOT).free < 15 * 1024**3:
        raise RuntimeError("Less than15GBdiskspace remains")
    index_path = Path(
        "/Users/andreykuronskin/keys_champ/data/additional/all-regions-osm/raw/geofabrik-index-v1.json"
    )
    feature = next(
        feature
        for feature in json.loads(index_path.read_text())["features"]
        if feature["properties"].get("id") == "south-fed-district"
    )
    geography_pbf.VectorHandler = Progress
    if not CACHE.exists() and not CACHE.with_name(CACHE.name + ".incomplete").exists():
        state("building", pbf_bytes=SOURCE.stat().st_size)
        try:
            geography_pbf.build_vector_cache(
                SOURCE, CACHE, coverage=feature["geometry"]
            )
        except ValueError:
            if not CACHE.with_name(CACHE.name + ".incomplete").exists():
                raise
    if not CACHE.exists():
        incomplete = CACHE.with_name(CACHE.name + ".incomplete")
        with sqlite3.connect(incomplete) as db:
            manifest = json.loads(
                db.execute(
                    "SELECT value FROM metadata WHERE key='manifest'"
                ).fetchone()[0]
            )
            manifest["coverage_source"] = {
                "url": "https://download.geofabrik.de/index-v1.json",
                "sha256": hashlib.sha256(index_path.read_bytes()).hexdigest(),
                "feature_id": "south-fed-district",
            }
            db.execute(
                "UPDATE metadata SET value=? WHERE key='manifest'",
                (json.dumps(manifest),),
            )
        repairs = ROOT / "repairs"
        repairs.mkdir(exist_ok=True)
        downloads = []
        state("repairing", missing=manifest["missing_areas"])
        for missing in manifest["missing_areas"]:
            osm_id, kind = missing["osm_id"], missing["kind"]
            path = repairs / f"{osm_id}.osm"
            prior = MAIN / "vector-cache-repairs" / path.name
            url = f"https://api.openstreetmap.org/api/0.6/{kind}/{osm_id}/full"
            if not path.exists() and prior.exists():
                shutil.copyfile(prior, path)
            if not path.exists():
                for attempt in range(3):
                    try:
                        record = download_object(url, path)
                        break
                    except HTTPError as error:
                        if error.code not in (429, 502, 503, 504) or attempt == 2:
                            raise
                        time.sleep(30)
            record = {
                "url": url,
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                "bytes": path.stat().st_size,
            }
            downloads.append(record)
            (repairs / "downloads.json").write_text(json.dumps(downloads, indent=2))
            state(
                "repairing",
                completed=len(downloads),
                total=len(manifest["missing_areas"]),
            )
        repair_vector_cache(incomplete, CACHE, repairs)
    state("merging", south_bytes=CACHE.stat().st_size)
    union = ROOT / "vector-cache-union.sqlite"
    if not union.exists():
        merged = merge_vector_caches([MAIN / "vector-cache.sqlite", CACHE], union)
    else:
        with sqlite3.connect(union) as db:
            merged = json.loads(
                db.execute(
                    "SELECT value FROM metadata WHERE key='manifest'"
                ).fetchone()[0]
            )
    coverage = shape(merged["coverage_geometry"])
    with sqlite3.connect(
        (MAIN / "queue.sqlite3").resolve().as_uri() + "?mode=ro", uri=True
    ) as db:
        tiles = [
            (identifier, json.loads(bounds))
            for identifier, bounds, regions in db.execute(
                "SELECT id,bbox,region_ids FROM tiles WHERE active=1"
            )
            if "07000000" in json.loads(regions)
        ]
    uncovered = [
        identifier for identifier, bounds in tiles if not coverage.covers(box(*bounds))
    ]
    if uncovered:
        raise ValueError(
            f"Union source coverage still missesStavropoltiles:{uncovered}"
        )
    state("publishing", covered_stavropol_tiles=len(tiles), bytes=union.stat().st_size)
    destination = MAIN / "vector-cache-union.sqlite"
    if destination.exists():
        raise ValueError("Root union artifact already exists; preserve it for review")
    temporary = destination.with_suffix(".sqlite.publishing")
    shutil.copyfile(union, temporary)
    temporary.replace(destination)
    (MAIN / "vector-cache-union.manifest.json").write_text(
        json.dumps(merged, ensure_ascii=False, indent=2)
    )
    sources = MAIN / "vector-sources"
    sources.mkdir(exist_ok=True)
    shutil.copyfile(SOURCE, sources / SOURCE.name)
    if (ROOT / "repairs").exists():
        shutil.copytree(
            ROOT / "repairs", MAIN / "vector-cache-south-repairs", dirs_exist_ok=True
        )
    state(
        "complete",
        output=str(destination),
        bytes=destination.stat().st_size,
        features=merged["features"],
        covered_stavropol_tiles=len(tiles),
    )


if __name__ == "__main__":
    try:
        main()
    except BaseException as error:
        state("failed", error=f"{type(error).__name__}: {error}")
        raise
