import argparse
import hashlib
import json
import re
from pathlib import Path

from app.domain.normative.model import Facility
from stamp_normative_sources import build

OSM_URL = "https://download.openstreetmap.fr/extracts/russia/ural_federal_district/kurgan_oblast-latest.osm.pbf"


def geocoder_snapshot(row: dict, raw: bytes) -> tuple[str, str]:
    entries = json.loads(raw)
    if not entries or float(entries[0]["lat"]) != row["latitude"] or float(entries[0]["lon"]) != row["longitude"]:
        raise ValueError("Cached geocoder response differs from the facility coordinates")
    return hashlib.sha256(raw).hexdigest(), row["coordinate_source"]


def geometry_method(row: dict, actual: dict) -> str:
    choices = [(actual, actual["geometry_method"]), (actual["area_centroid"], "area_centroid")]
    for coordinates, method in choices:
        if all(abs(coordinates[key] - row[key]) <= 0.000000051 for key in ("latitude", "longitude")):
            return method
    raise ValueError("Facility geometry does not reproduce from the referenced OSM object")


def stamp(row: dict, digest: str, url: str) -> dict:
    if row.get("coordinate_snapshot_sha256") not in (None, digest) or row.get("coordinate_snapshot_url") not in (None, url):
        raise ValueError("Coordinate snapshot conflicts with existing provenance")
    result = {**row, "coordinate_snapshot_sha256": digest, "coordinate_snapshot_url": url}
    Facility(**result)
    return result


def verified_datasets(root: Path) -> list[tuple[Path, dict]]:
    municipal = {key: build(root, key)[1] for key in ("schools", "libraries", "stops")}
    pbf = (root / ".local/normative-inputs/kurgan.osm.pbf").read_bytes()
    pbf_digest = hashlib.sha256(pbf).hexdigest()
    fire = json.loads((root / "datasets/normative-fire-coordinate-candidates.json").read_text())
    medical = json.loads((root / "datasets/normative-medical-osm-candidates.json").read_text())
    geometry = json.loads((root / "datasets/normative-coordinate-snapshot-records.json").read_text())
    if geometry["pbf_sha256"] != pbf_digest:
        raise ValueError("Coordinate object records belong to another extract")
    indexed = {f"https://www.openstreetmap.org/{r['kind']}/{r['id']}": r for r in geometry["records"]}
    result = []
    for path in sorted((root / "datasets/normative").glob("*.json")):
        if path.name == "criteria.json":
            continue
        document = json.loads(path.read_text())
        rows = []
        for row in document["facilities"]:
            digest, url = None, None
            if row["latitude"] is not None and row["longitude"] is not None:
                source = row["coordinate_source"] or ""
                if path.stem in municipal and source == municipal[path.stem]["url"]:
                    digest, url = municipal[path.stem]["sha256"], source
                elif re.fullmatch(r"https://www\.openstreetmap\.org/(?:node|way)/[0-9]+", source):
                    expected = fire.get("pbf_sha256") if path.stem == "fire" else document.get("coordinate_extract_sha256")
                    if expected != pbf_digest:
                        raise ValueError("OSM coordinate source differs from the saved extract")
                    actual = indexed.get(source)
                    if actual is None:
                        raise ValueError("Coordinate source object is absent from the extract")
                    geometry_method(row, actual)
                    records = fire["facilities"] if path.stem == "fire" else medical["facilities"] if path.stem == "medical" else None
                    if records is not None:
                        matches = [r for r in records if r["id"] == row["id"]]
                        if len(matches) != 1 or any(matches[0][key] != row[key] for key in ("latitude", "longitude", "coordinate_source")):
                            raise ValueError("OSM coordinates differ from the reviewed source records")
                    digest, url = pbf_digest, OSM_URL
                elif source.startswith("https://nominatim.openstreetmap.org/search?"):
                    cache = root / ".local/normative-sources" / (hashlib.sha256(source.encode()).hexdigest() + ".json")
                    if cache.exists():
                        digest, url = geocoder_snapshot(row, cache.read_bytes())
            if digest is not None and url is not None:
                row = stamp(row, digest, url)
            Facility(**row)
            rows.append(row)
        result.append((path, {**document, "facilities": rows}))
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args()
    results = verified_datasets(args.root)
    for path, document in results:
        path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n")
        print(path.name, sum(bool(r.get("coordinate_snapshot_sha256")) for r in document["facilities"]))


if __name__ == "__main__":
    main()
