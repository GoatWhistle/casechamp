import argparse
import hashlib
import json
import re
from datetime import UTC, datetime
from html import unescape
from pathlib import Path

from normative_sources import download, geocode, text

SERVICES = {"schools": "school", "libraries": "library", "stops": "stop"}


def municipal_service(service: str, name: str) -> str:
    if service != "library":
        return service
    lowered = name.lower()
    if "областн" in lowered and "библиотек" in lowered:
        return "regional_library"
    if "медицинский информационно-аналитический центр" in lowered or "кгсха" in lowered:
        return "institutional_library"
    if "детск" in lowered:
        return "children_library"
    return service


def municipal(records: list[dict], source: dict, service: str) -> list[dict]:
    entries = []
    for row in records:
        fields = row["fields"]
        geometry = row.get("geom", {})
        if geometry.get("type") != "Point":
            raise ValueError("Unexpected municipal geometry")
        lon, lat = geometry["coordinates"]
        if not (54 < lat < 57 and 61 < lon < 69):
            raise ValueError("Municipal coordinates outside the source territory")
        name = fields.get("ie_name") or fields.get("description")
        if not name:
            raise ValueError("Missing municipal object name")
        entries.append({
            "id": f"kurgan-{service}-{row['id']}",
            "service": municipal_service(service, name),
            "name": unescape(name),
            "address": unescape(fields.get("ip_prop723") or fields.get("addr") or ""),
            "source_url": source["url"],
            "source_sha256": source.get("sha256"),
            "observed_at": source["received_at"],
            "latitude": lat,
            "longitude": lon,
            "coordinate_source": source["url"],
            "coordinate_status": "official_institution_pin",
        })
    return entries


def employment(html: str, source: dict) -> list[dict]:
    pattern = r'<ol[^>]*>(.*?)</ol>\s*<p[^>]*>Адрес:\s*(.*?)</p>'
    rows = re.findall(pattern, html, re.S)
    entries = []
    for name, raw_address in rows:
        address = re.split(r"[\w.+-]+@[\w.-]+", text(raw_address))[0].strip(" ,;")
        entries.append({
            "id": "employment-" + hashlib.sha256(address.encode()).hexdigest()[:12],
            "service": "employment",
            "name": text(name),
            "address": address,
            "source_url": source["url"],
            "source_sha256": source.get("sha256"),
            "observed_at": source["received_at"],
        })
    if len(entries) != 24:
        raise ValueError(f"Unexpected employment directory size: {len(entries)}")
    return entries


def station(records: dict, source: dict) -> list[dict]:
    if records["count"] != len(records["items"]):
        raise ValueError("Bus station response is paginated")
    return [{
        "id": "bus-station-" + row["registrationNumber"],
        "service": "bus_station",
        "name": row["name"],
        "address": row["address"],
        "source_url": source["url"],
            "source_sha256": source.get("sha256"),
        "observed_at": source["received_at"],
    } for row in records["items"] if row["type"] in ("0", "1")]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, default=Path(".local/normative-inputs"))
    parser.add_argument("--geocode", action="store_true")
    parser.add_argument("--download", action="store_true")
    args = parser.parse_args()
    if args.download:
        args.input.mkdir(parents=True, exist_ok=True)
        manifest = json.loads(Path("datasets/normative-sources.json").read_text())
        for source in manifest:
            raw = download(source["url"])
            (args.input / (source["id"] + ".raw")).write_bytes(raw)
            source.update(sha256=hashlib.sha256(raw).hexdigest(), bytes=len(raw),
                          received_at=datetime.now(UTC).isoformat())
        (args.input / "manifest.json").write_text(json.dumps(manifest, indent=2))
    manifest = json.loads((args.input / "manifest.json").read_text())
    cache = Path(".local/normative-sources")
    cache.mkdir(parents=True, exist_ok=True)
    for source in manifest:
        key = source["id"]
        if key == "mfc-city":
            continue
        raw = (args.input / (key + ".raw")).read_bytes()
        if hashlib.sha256(raw).hexdigest() != source["sha256"]:
            raise ValueError(f"Input hash mismatch: {key}")
        if key in SERVICES:
            entries = municipal(json.loads(raw), source, SERVICES[key])
        elif key == "employment":
            entries = employment(raw.decode(), source)
        elif key == "bus-stations":
            entries = station(json.loads(raw), source)
        else:
            raise ValueError(f"Unsupported source: {key}")
        for entry in entries:
            if "latitude" in entry:
                continue
            query = re.sub(r"\b\d{6}\b,?", "", entry["address"])
            query = re.sub(r"Курганская\s+(?:область|обл\.)[,]?", "", query)
            lat, lon, url = geocode(query.strip(" ,"), cache) if args.geocode else (None, None, None)
            entry.update(latitude=lat, longitude=lon, coordinate_source=url,
                         coordinate_status="geocoded_building" if url else "missing")
        output = {**source, "complete_inventory": False, "facilities": entries}
        Path(f"datasets/normative/{key}.json").write_text(
            json.dumps(output, ensure_ascii=False, indent=2) + "\n"
        )
        print(key, len(entries), sum(e["latitude"] is not None for e in entries), flush=True)


if __name__ == "__main__":
    main()
