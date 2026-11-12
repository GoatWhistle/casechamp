import hashlib
import json
import subprocess
from datetime import UTC, datetime
from pathlib import Path

BASE = "https://download.openstreetmap.fr/extracts/russia/"
DISTRICTS = ("central", "far_eastern", "north_caucasian", "northwestern", "siberian", "southern", "ural", "volga")
SOURCES = [(name + "_federal_district", BASE) for name in DISTRICTS] + [
    ("crimea", "https://download.openstreetmap.fr/extracts/europe/ukraine/"),
    ("sevastopol", "https://download.openstreetmap.fr/extracts/europe/ukraine/"),
]
ROOT = Path(__file__).resolve().parents[1] / ".local/normative-national-inputs/osm"


def download(url: str, path: Path) -> None:
    subprocess.run(["curl", "--fail", "--location", "--retry", "3", "--max-time", "3600", "--silent", "--show-error", "--output", str(path), url], check=True)


def digest_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    ROOT.mkdir(parents=True, exist_ok=True)
    manifest_path = ROOT / "manifest.json"
    manifest = json.loads(manifest_path.read_text()) if manifest_path.exists() else []
    for key, base in SOURCES:
        path = ROOT / (key + ".osm.pbf")
        known = next((r for r in manifest if r["id"] == key), None)
        if known and path.exists() and path.stat().st_size == known["bytes"]:
            if digest_file(path) != known["sha256"]:
                raise ValueError("Cached OSM extract hash differs from its manifest")
            print("cached", key, known["bytes"], flush=True)
            continue
        before = ROOT / (key + ".state.before.txt")
        after = ROOT / (key + ".state.txt")
        download(base + key + ".state.txt", before)
        part = path.with_suffix(path.suffix + ".part")
        print("downloading", key, flush=True)
        download(base + key + "-latest.osm.pbf", part)
        download(base + key + ".state.txt", after)
        if before.read_bytes() != after.read_bytes():
            raise ValueError("OSM extract state changed during download")
        digest = digest_file(part)
        with part.open("rb") as stream:
            length = int.from_bytes(stream.read(4), "big")
            if not 0 < length < 65536 or b"OSMHeader" not in stream.read(length):
                raise ValueError("Downloaded file is not an OSM PBF")
        if part.stat().st_size < 1000000:
            raise ValueError("OSM district extract is unexpectedly small")
        part.replace(path)
        record = {"id": key, "url": base + key + "-latest.osm.pbf", "bytes": path.stat().st_size,
                  "sha256": digest, "received_at": datetime.now(UTC).isoformat(),
                  "state": after.read_text().strip(), "licence": "ODbL-1.0"}
        manifest = [r for r in manifest if r["id"] != key] + [record]
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n")
        print("downloaded", key, record["bytes"], record["sha256"], flush=True)


if __name__ == "__main__":
    main()
