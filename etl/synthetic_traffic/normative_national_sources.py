import json
import os
import shutil
from pathlib import Path

import acquire_normative_national as acquisition
import osmium


def seed_existing(repo, external_root):
    repo, external_root = Path(repo), Path(external_root)
    root = repo / ".local/normative-national-inputs"
    (root / "osm").mkdir(parents=True, exist_ok=True)
    (root / "derived").mkdir(exist_ok=True)
    boundary = repo / "data/traffic-geography-national/boundaries.json"
    if not (root / "regions.json").exists():
        shutil.copyfile(boundary, root / "regions.json")
    known = (
        json.loads((root / "osm/manifest.json").read_text())
        if (root / "osm/manifest.json").exists()
        else []
    )
    sources = [
        (
            "north_caucasian_federal_district",
            repo / "data/additional/stavropol/raw/north-caucasus-261107.osm.pbf",
            "https://download.geofabrik.de/russia/north-caucasus-fed-district-261107.osm.pbf",
        ),
        (
            "southern_federal_district",
            repo
            / "data/traffic-geography-national/vector-sources/south-fed-district-261111.osm.pbf",
            "https://download.geofabrik.de/russia/south-fed-district-261111.osm.pbf",
        ),
        (
            "ural_federal_district",
            repo / "data/additional/osm-ural/raw/ural-fed-district-261106.osm.pbf",
            "https://download.geofabrik.de/russia/ural-fed-district-261106.osm.pbf",
        ),
        (
            "crimea",
            external_root / "crimean-fed-district.osm.pbf",
            "https://download.geofabrik.de/russia/crimean-fed-district-latest.osm.pbf",
        ),
    ]
    for key, path, url in sources:
        if any(row["id"] == key for row in known) or not path.is_file():
            continue
        target = root / "osm" / (key + ".osm.pbf")
        if not target.exists():
            os.link(path, target)
        with osmium.io.Reader(str(path)) as reader:
            timestamp = reader.header().get("osmosis_replication_timestamp")
        known.append(
            {
                "id": key,
                "url": url,
                "bytes": path.stat().st_size,
                "sha256": acquisition.digest_file(path),
                "received_at": timestamp,
                "state": "timestamp=" + timestamp,
                "licence": "ODbL-1.0",
                "reused_existing_source": True,
            }
        )
    (root / "osm/manifest.json").write_text(json.dumps(known, indent=2))
