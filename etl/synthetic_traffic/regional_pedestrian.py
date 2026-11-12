import argparse
import hashlib
import json
import os
from datetime import UTC, datetime
from pathlib import Path

import osmium
import pyarrow as pa
import pyarrow.parquet as pq
from analytics.client import ClickHouse
from normative_walking.extract import Extractor
from shapely import intersects_xy, make_valid
from shapely.geometry import shape

RULES = "pedestrian-v2"


def prepare_pedestrian(pbf, source_url, region, output, client=None):
    pbf, output = Path(pbf), Path(output)
    digest = hashlib.sha256(pbf.read_bytes()).hexdigest()
    region_hash = hashlib.sha256(
        json.dumps(region, sort_keys=True).encode()
    ).hexdigest()
    revision = hashlib.sha256((digest + RULES + region_hash).encode()).hexdigest()[:24]
    folder = output / revision
    folder.mkdir(parents=True, exist_ok=True)
    with osmium.io.Reader(str(pbf)) as reader:
        timestamp = reader.header().get("osmosis_replication_timestamp")
    if not timestamp:
        raise ValueError("Pedestrian source requires an original PBF timestamp")
    manifest_path = folder / "manifest.json"
    if manifest_path.exists():
        metadata = json.loads(manifest_path.read_text())
        if metadata["source_sha256"] != digest:
            raise ValueError("Pedestrian source cache mismatch")
    else:
        handler = Extractor(folder, revision)
        handler.apply_file(
            str(pbf),
            locations=True,
            idx="flex_mem",
            filters=[osmium.filter.KeyFilter("highway", "building", "barrier", "foot")],
        )
        counts = handler.finish(folder)
        origins = pq.read_table(folder / "origins.parquet")
        polygon = make_valid(
            shape({"type": "MultiPolygon", "coordinates": region["polygons"]})
        )
        selected = intersects_xy(
            polygon, origins["longitude"].to_numpy(), origins["latitude"].to_numpy()
        )
        filtered = origins.filter(pa.array(selected))
        pq.write_table(filtered, folder / "origins.parquet")
        if not len(filtered) or not counts["nodes"] or not counts["edges"]:
            raise ValueError(
                "Source does not contain usable pedestrian roads and residential origins"
            )
        metadata = {
            "revision": revision,
            "created_at": datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S.%f"),
            "source_url": source_url,
            "source_sha256": digest,
            "source_timestamp": timestamp,
            "rules_version": RULES,
            "node_count": counts["nodes"],
            "edge_count": counts["edges"],
            "origin_count": len(filtered),
            "excluded_counts": {
                **{
                    key: value
                    for key, value in counts.items()
                    if key not in {"nodes", "edges", "residential_buildings"}
                },
                "residential_origins_outside_selected_region": len(origins)
                - len(filtered),
            },
        }
        manifest_path.write_text(json.dumps(metadata, indent=2))
    if client is None:
        return metadata
    if client.rows(
        "SELECT revision FROM plexus_normative.pedestrian_networks WHERE revision='"
        + revision
        + "' LIMIT 1"
    ):
        print("Pedestrian snapshot already imported", revision, flush=True)
        return metadata
    for name in ("nodes", "edges", "origins"):
        table = "plexus_normative.pedestrian_" + name
        if int(
            client.rows(
                "SELECT count() AS n FROM "
                + table
                + " WHERE revision='"
                + revision
                + "'"
            )[0]["n"]
        ):
            raise ValueError(
                "Partial unpublished pedestrian import exists; inspect before retrying"
            )
    for name in ("nodes", "edges", "origins"):
        client.parquet(
            "plexus_normative.pedestrian_" + name, folder / (name + ".parquet")
        )
    client.request(
        "INSERT INTO plexus_normative.pedestrian_networks FORMAT JSONEachRow",
        json.dumps(metadata).encode(),
    )
    binding = {
        "region_id": region["id"],
        "region_name": region["name"],
        "purpose": "physical",
        "revision": revision,
        "published_at": metadata["created_at"],
        "boundary_sha256": region_hash,
    }
    client.request(
        "INSERT INTO plexus_normative.pedestrian_regions FORMAT JSONEachRow",
        json.dumps(binding, ensure_ascii=False).encode(),
    )
    print("Pedestrian snapshot imported", json.dumps(metadata), flush=True)
    return metadata


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pbf", type=Path, required=True)
    parser.add_argument("--source-url", required=True)
    parser.add_argument("--regions", type=Path, required=True)
    parser.add_argument("--region", required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--env", type=Path)
    parser.add_argument("--import-storage", action="store_true")
    args = parser.parse_args()
    if args.env:
        for line in args.env.read_text().splitlines():
            if "=" in line and not line.lstrip().startswith("#"):
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip().strip("\"'")
    region = next(
        row
        for row in json.loads(args.regions.read_text())["regions"]
        if row["id"] == args.region
    )
    client = ClickHouse() if args.import_storage else None
    result = prepare_pedestrian(args.pbf, args.source_url, region, args.output, client)
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
