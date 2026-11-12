import argparse
import hashlib
import json
import math
import re
from datetime import date, datetime
from pathlib import Path

from normative_address import normalized


def directory_facilities(
    source: dict, candidates: dict, pdf: bytes
) -> tuple[list[dict], list[dict]]:
    if source.get("snapshot_kind") != "reviewed_pdf_address_rows":
        raise ValueError("Fire directory requires reviewed primary PDF rows")
    if not source["source_url"].startswith("https://45.mchs.gov.ru/"):
        raise ValueError("Fire addresses require their primary source")
    observed = datetime.fromisoformat(source["observed_at"])
    if len(source["observed_at"]) > 10 and observed.tzinfo is None:
        raise ValueError("Timestamped source observations require a timezone")
    if (
        hashlib.sha256(pdf).hexdigest() != source["pdf_sha256"]
        or len(pdf) != source["pdf_bytes"]
    ):
        raise ValueError("Fire source PDF does not match the reviewed snapshot")
    if (
        source.get("inventory_status") != "partial"
        or source.get("operational_status") != "unconfirmed"
    ):
        raise ValueError(
            "A contact directory cannot establish a complete operational inventory"
        )
    coordinate_records = candidates["facilities"]
    coordinates = {row["id"]: row for row in coordinate_records}
    if len(coordinates) != len(coordinate_records):
        raise ValueError("Duplicate fire coordinate candidates")
    records = source["records"]
    if not records or len(records) != source["address_rows_reviewed"]:
        raise ValueError("Fire address rows differ from the reviewed source count")
    if len({row["id"] for row in records}) != len(records) or set(coordinates) - {
        row["id"] for row in records
    }:
        raise ValueError("Duplicate primary rows or orphan coordinate candidates")
    result = []
    exclusions = []
    for record in records:
        key = record["id"]
        if not re.fullmatch(r"(?:psch-[0-9]{2}|spsch-mamontov)", key):
            raise ValueError("Unsupported fire unit identifier")
        if (
            not record["name"].strip()
            or not record["source_address"].strip()
            or not record["address"].strip()
        ):
            raise ValueError("Fire records require reviewed names and addresses")
        page = record["source_page"]
        if type(page) is not int or not 1 <= page <= source["pdf_pages"]:
            raise ValueError("Fire source page is outside the reviewed PDF")
        if record["address_status"] not in {"complete", "house_missing"}:
            raise ValueError("Unknown fire address review status")
        facility = {
            "id": key,
            "service": "fire",
            "name": record["name"],
            "address": record["address"],
            "source_url": source["source_url"] + "#page=" + str(page),
            "observed_at": source["observed_at"],
            "latitude": None,
            "longitude": None,
            "coordinate_source": None,
            "coordinate_status": "missing",
            "published_on": None,
            "source_sha256": source["pdf_sha256"],
        }
        candidate = coordinates.get(key)
        if candidate is not None:
            validate_candidate(candidate)
            if record["address_status"] != "complete":
                exclusions.append({"id": key, "reason": "primary_house_missing"})
            elif normalized(candidate["address"]) != normalized(record["address"]):
                facility["coordinate_status"] = "address_conflict"
                exclusions.append({"id": key, "reason": "primary_address_mismatch"})
            else:
                for field in (
                    "latitude",
                    "longitude",
                    "coordinate_source",
                    "coordinate_status",
                ):
                    facility[field] = candidate[field]
        result.append(facility)
    return result, exclusions


def validate_candidate(candidate: dict) -> None:
    if (
        candidate["service"] != "fire"
        or candidate["coordinate_status"] != "osm_fire_building_exit_unverified"
    ):
        raise ValueError(
            "Only reviewed unverified fire coordinate candidates may be reused"
        )
    date.fromisoformat(candidate["observed_at"])
    if not re.fullmatch(
        r"https://www\.openstreetmap\.org/(?:node|way)/[0-9]+",
        candidate["coordinate_source"],
    ):
        raise ValueError("Fire coordinate candidates require their exact OSM source")
    for key, limit in (("latitude", 90), ("longitude", 180)):
        value = candidate[key]
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or abs(value) > limit
        ):
            raise ValueError("Invalid fire coordinate candidate")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("datasets/normative-fire-source-records.json"),
    )
    parser.add_argument(
        "--coordinates",
        type=Path,
        default=Path("datasets/normative-fire-coordinate-candidates.json"),
    )
    parser.add_argument(
        "--pdf", type=Path, default=Path(".local/research/fire-directory-2025.pdf")
    )
    parser.add_argument(
        "--output", type=Path, default=Path("datasets/normative/fire.json")
    )
    args = parser.parse_args()
    raw = args.input.read_bytes()
    source = json.loads(raw)
    candidates = json.loads(args.coordinates.read_bytes())
    facilities, exclusions = directory_facilities(
        source, candidates, args.pdf.read_bytes()
    )
    result = {
        "source_url": source["source_url"],
        "source_publication_date": None,
        "url_upload_date": source["url_upload_date"],
        "observed_at": source["observed_at"],
        "inventory_status": "partial",
        "current_service_verified": False,
        "pdf_sha256": source["pdf_sha256"],
        "pdf_bytes": source["pdf_bytes"],
        "extracted_fields_sha256": hashlib.sha256(raw).hexdigest(),
        "coordinate_licence": candidates["coordinate_licence"],
        "pbf_sha256": candidates["pbf_sha256"],
        "coordinate_exclusions": exclusions,
        "facilities": facilities,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(
        "fire directory",
        len(facilities),
        "coordinates",
        sum(row["latitude"] is not None for row in facilities),
    )


if __name__ == "__main__":
    main()
