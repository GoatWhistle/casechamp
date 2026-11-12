import argparse
import hashlib
import json
from pathlib import Path

from normative_civic_sources import employment, municipal, station
from normative_sources import departments

SOURCES = ("schools", "libraries", "stops", "employment", "bus-stations", "mfc")
FIELDS = ("service", "name", "address", "source_url")


def verified_document(raw: bytes, document: dict, records: list[dict]) -> dict:
    digest = hashlib.sha256(raw).hexdigest()
    if digest != document.get("sha256"):
        raise ValueError("Source bytes do not match the recorded document hash")
    if "bytes" in document and len(raw) != document["bytes"]:
        raise ValueError("Source byte length does not match the recorded document")
    expected = {record["id"]: record for record in records}
    facilities = document["facilities"]
    if len(expected) != len(records) or len({f["id"] for f in facilities}) != len(facilities):
        raise ValueError("Source identifiers must be unique")
    if expected.keys() != {f["id"] for f in facilities}:
        raise ValueError("Source records differ from the facility inventory")
    observed = document.get("received_at", document.get("observed_at"))
    if not observed:
        raise ValueError("Source observation date is missing")
    stamped = []
    for facility in facilities:
        original = expected[facility["id"]]
        if any(original.get(field) != facility.get(field) for field in FIELDS):
            raise ValueError("Facility address fields differ from the source document")
        if facility["observed_at"] != observed:
            raise ValueError("Facility observation differs from the source document")
        for field in ("latitude", "longitude", "coordinate_source"):
            if field in original and original[field] != facility.get(field):
                raise ValueError("Official coordinates differ from the source document")
        if facility.get("source_sha256") not in (None, digest):
            raise ValueError("Existing source hash conflicts with the verified document")
        stamped.append({**facility, "source_sha256": digest})
    return {**document, "facilities": stamped}


def build(root: Path, key: str) -> tuple[Path, dict]:
    path = root / f"datasets/normative/{key}.json"
    document = json.loads(path.read_text())
    if key == "mfc":
        raw = (root / ".local/normative-sources/mfc-map.html").read_bytes()
        records = departments(raw.decode())
    else:
        manifest = json.loads((root / ".local/normative-inputs/manifest.json").read_text())
        sources = [source for source in manifest if source["id"] == key]
        if len(sources) != 1 or any(
            document.get(field) != sources[0].get(field)
            for field in ("url", "sha256", "bytes", "received_at")
        ):
            raise ValueError("Facility document differs from the acquisition manifest")
        raw = (root / f".local/normative-inputs/{key}.raw").read_bytes()
        services = {"schools": "school", "libraries": "library", "stops": "stop"}
        if key in services:
            records = municipal(json.loads(raw), document, services[key])
        elif key == "employment":
            records = employment(raw.decode(), document)
        elif key == "bus-stations":
            records = station(json.loads(raw), document)
        else:
            raise ValueError("Unsupported source snapshot")
    return path, verified_document(raw, document, records)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parent.parent)
    args = parser.parse_args()
    results = [build(args.root, key) for key in SOURCES]
    for path, document in results:
        path.write_text(json.dumps(document, ensure_ascii=False, indent=2) + "\n")
        print(path.name, len(document["facilities"]), document["sha256"])


if __name__ == "__main__":
    main()
