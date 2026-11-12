import argparse
import json
import os
import time
from pathlib import Path

from analytics.client import ClickHouse
from shapely.geometry import shape

SCHEMA = """CREATE TABLE IF NOT EXISTS plexus_atlas.municipal_boundaries (id String,region_id String,name String,admin_level UInt8,osm_relation_id Int64,geometry_json String,bounds Tuple(Float64,Float64,Float64,Float64),source_url String,observed_at String,source_sha256 String,region_assignment String,region_overlap_fraction Float64,version UInt64) ENGINE=ReplacingMergeTree(version) ORDER BY(region_id,id)"""
FIELDS = (
    "id",
    "region_id",
    "name",
    "admin_level",
    "osm_relation_id",
    "source_url",
    "observed_at",
    "source_sha256",
    "region_assignment",
    "region_overlap_fraction",
)


def prepare_import(features, existing, version):
    records, skipped = [], 0
    for feature in features:
        properties = feature["properties"]
        record = {key: properties[key] for key in FIELDS}
        geometry = shape(feature["geometry"])
        if (
            geometry.geom_type != "MultiPolygon"
            or geometry.is_empty
            or not geometry.is_valid
        ):
            raise ValueError("Municipal import requires valid original MultiPolygons")
        if (
            not properties["id"]
            or not properties["name"]
            or not properties["region_id"]
        ):
            raise ValueError(
                "Municipal import requires exact source identity and region attribution"
            )
        record["geometry_json"] = json.dumps(feature["geometry"], separators=(",", ":"))
        record["bounds"] = list(geometry.bounds)
        record["version"] = version
        previous = existing.get(record["id"])
        if previous is not None:
            if previous["region_id"] != record["region_id"]:
                raise ValueError(
                    "Stable municipal ID changed region; explicit migration required"
                )
            if previous["observed_at"] > record["observed_at"]:
                skipped += 1
                continue
            if previous["observed_at"] == record["observed_at"]:
                if previous["source_sha256"] != record["source_sha256"]:
                    raise ValueError(
                        "Conflicting source snapshot for the same municipal ID and date"
                    )
                skipped += 1
                continue
        existing[record["id"]] = record
        records.append(record)
    return records, skipped


def import_files(paths, env_file=None):
    if env_file is not None:
        for line in Path(env_file).read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip().strip("\"'")
    client = ClickHouse()
    client.request(SCHEMA)
    existing = {
        row["id"]: row
        for row in client.rows(
            "SELECT id,region_id,observed_at,source_sha256 FROM plexus_atlas.municipal_boundaries FINAL"
        )
    }
    features = [
        feature
        for path in paths
        for feature in json.loads(Path(path).read_text())["features"]
    ]
    records, skipped = prepare_import(features, existing, time.time_ns())
    for start in range(0, len(records), 25):
        payload = "\n".join(
            json.dumps(record, ensure_ascii=False)
            for record in records[start : start + 25]
        ).encode()
        client.request(
            "INSERT INTO plexus_atlas.municipal_boundaries SETTINGS max_threads=1,max_insert_threads=1,input_format_parallel_parsing=0 FORMAT JSONEachRow",
            payload,
        )
    return {
        "inserted": len(records),
        "skipped": skipped,
        "counts_by_region": client.rows(
            "SELECT region_id,count() AS features FROM plexus_atlas.municipal_boundaries FINAL GROUP BY region_id ORDER BY region_id"
        ),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--file", type=Path, action="append", required=True)
    parser.add_argument("--env", type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    result = import_files(args.file, args.env)
    value = json.dumps(result, ensure_ascii=False, indent=2)
    if args.report:
        args.report.write_text(value)
    print(value)


if __name__ == "__main__":
    main()
