import argparse
import hashlib
import json
import re
from datetime import UTC, date, datetime
from pathlib import Path

from normative_civic_sources import municipal_service
from normative_library_deduplication import deduplicate


def directory_facilities(source: dict, observed_at: str) -> tuple[list[dict], list[dict]]:
    date.fromisoformat(source["reviewed_on"])
    datetime.fromisoformat(observed_at)
    if source.get("snapshot_kind") != "reviewed_web_reader_fields":
        raise ValueError("Library records require reviewed source fields")
    facilities = []
    excluded = []
    seen = set()
    for record in source["records"]:
        url = record["source_url"]
        match = re.fullmatch(r"https://yugovalib\.ru/site/view/(\d+)", url)
        if not match or url in seen:
            raise ValueError("Library card URLs must be unique primary sources")
        seen.add(url)
        date.fromisoformat(record["published_on"])
        name = record["name"].strip()
        address = record["address"]
        profile = record.get("profile_hint", municipal_service("library", name))
        if profile not in {
            "library",
            "children_library",
            "regional_library",
            "institutional_library",
            "library_service_point",
            "other",
        }:
            raise ValueError("Unknown library profile")
        status = record.get("read_status", "read")
        operation = record.get("operational_status", "unconfirmed")
        if status not in {"read", "unavailable", "address_missing", "ambiguous"}:
            raise ValueError("Unknown library source review status")
        if operation not in {"unconfirmed", "explicitly_closed"}:
            raise ValueError("Unknown library operational status")
        if operation == "explicitly_closed":
            excluded.append({"source_url": url, "reason": "explicitly_closed"})
            continue
        if status != "read":
            excluded.append({"source_url": url, "reason": status})
            continue
        if profile == "other" or ("profile_hint" not in record and "библиотек" not in name.lower()):
            excluded.append({"source_url": url, "reason": "different_institution_type"})
            continue
        if not address or not address.strip():
            excluded.append({"source_url": url, "reason": "missing_address"})
            continue
        facilities.append(
            {
                "id": "yugov-library-" + match[1],
                "service": profile,
                "name": name,
                "address": address.strip(),
                "source_url": url,
                "observed_at": observed_at,
                "latitude": None,
                "longitude": None,
                "coordinate_source": None,
                "coordinate_status": "missing",
                "published_on": record["published_on"],
            }
        )
    return facilities, excluded


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input", type=Path, default=Path("datasets/normative-library-source-records.json")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("datasets/normative/regional-libraries.json")
    )
    args = parser.parse_args()
    raw = args.input.read_bytes()
    source = json.loads(raw)
    observed_at = source["reviewed_on"]
    facilities, excluded = directory_facilities(source, observed_at)
    municipal_path = Path("datasets/normative/libraries.json")
    existing = json.loads(municipal_path.read_text())["facilities"]
    facilities, aliases = deduplicate(facilities, existing)
    result = {
        "source_url": source["source_url"],
        "observed_at": observed_at,
        "generated_at": datetime.now(UTC).isoformat(),
        "reviewed_on": source["reviewed_on"],
        "snapshot_kind": source["snapshot_kind"],
        "extracted_fields_sha256": hashlib.sha256(raw).hexdigest(),
        "complete_inventory": False,
        "current_service_verified": False,
        "source_records": source["records"],
        "unread_card_urls": source["unread_card_urls"],
        "excluded": excluded,
        "duplicate_sources": aliases,
        "facilities": facilities,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("library directory", len(facilities), "excluded", len(excluded))


if __name__ == "__main__":
    main()
