import json
from hashlib import sha256
from pathlib import Path

import osmium
import pyarrow.parquet as pq
from synthetic_traffic.download import download
from synthetic_traffic.housing_extract import extract

DISTRICTS = (
    "central-fed-district",
    "northwestern-fed-district",
    "south-fed-district",
    "north-caucasus-fed-district",
    "volga-fed-district",
    "ural-fed-district",
    "siberian-fed-district",
    "far-eastern-fed-district",
    "crimean-fed-district",
)


def collect(destination: Path) -> dict:
    destination.mkdir(parents=True, exist_ok=True)
    manifest_path = destination / "collection.json"
    manifest = (
        json.loads(manifest_path.read_text())
        if manifest_path.exists()
        else {"status": "running", "sources": {}}
    )
    for name in DISTRICTS:
        output = destination / f"{name}.parquet"
        record = manifest["sources"].get(name, {})
        if record.get("status") == "complete" and output.exists():
            if sha256(output.read_bytes()).hexdigest() != record["parquet_sha256"]:
                raise ValueError(f"Housing output changed: {name}")
            continue
        if output.exists():
            raise ValueError(f"Untracked housing output exists: {output}")
        url = f"https://download.geofabrik.de/russia/{name}-latest.osm.pbf"
        temporary = destination / f"{name}.download.pbf"
        print(f"Downloading {name}", flush=True)
        digest = download(url, temporary)
        reader = osmium.io.Reader(str(temporary))
        header = reader.header()
        timestamp = header.get("osmosis_replication_timestamp")
        reader.close()
        print(f"Extracting residential buildings: {name}", flush=True)
        counts = extract(temporary, output)
        if pq.read_metadata(output).num_rows != counts["residential_buildings"]:
            raise ValueError(f"Housing row verification failed: {name}")
        manifest["sources"][name] = {
            **counts,
            "url": url,
            "osm_timestamp": timestamp,
            "pbf_sha256": digest,
            "pbf_bytes": temporary.stat().st_size,
            "parquet_sha256": sha256(output.read_bytes()).hexdigest(),
            "status": "complete",
        }
        manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
        temporary.unlink()
        print(
            f"Completed {name}: {counts['residential_buildings']} buildings", flush=True
        )
    manifest["status"] = "complete"
    manifest["residential_records_before_cross_extract_deduplication"] = sum(
        row["residential_buildings"] for row in manifest["sources"].values()
    )
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    return manifest
