import argparse
import hashlib
import json
import math
import re
from datetime import date
from pathlib import Path

from normative_address import normalized
from normative_medical_matching import merge_coordinates, validate_osm_candidate

FORMS = {"экстренная": "emergency_cardiology", "неотложная": "urgent_cardiology", "плановая": None}
SOURCE_URL = "https://kurgan-med.ru/upload/iblock/838/tjdzs5h4gyy2g651go059a7gr08a1ifg.pdf"


def care_forms(value: str) -> list[str]:
    prefix, separator, _ = value.casefold().partition("кардиология")
    words = re.findall(r"[а-яё]+", prefix)
    if not separator or not words or any(word not in FORMS for word in words):
        raise ValueError("Care forms require an explicit reviewed cardiology cell")
    if len(set(words)) != len(words):
        raise ValueError("Duplicate cardiology care forms")
    return [form for word in words if (form := FORMS[word]) is not None]


def directory_facilities(source: dict, candidates: dict, pdf: bytes) -> tuple[list[dict], list[dict]]:
    if source.get("snapshot_kind") != "reviewed_pdf_cardiology_rows" or source.get("source_url") != SOURCE_URL:
        raise ValueError("Medical records require the reviewed primary PDF")
    date.fromisoformat(source["observed_at"])
    date.fromisoformat(source["act_date"])
    if source["act"] != "1469" or source["act_date"] != "2025-10-16":
        raise ValueError("Medical order identity differs from the reviewed first page")
    if hashlib.sha256(pdf).hexdigest() != source["pdf_sha256"] or len(pdf) != source["pdf_bytes"]:
        raise ValueError("Medical source PDF differs from the reviewed snapshot")
    if source.get("complete_current_inventory") is not False or source.get("operational_status") != "unconfirmed":
        raise ValueError("A historic table cannot establish a complete current inventory")
    records = source["records"]
    if len(records) != source["address_rows_reviewed"] or len({r["id"] for r in records}) != len(records):
        raise ValueError("Medical source rows require the reviewed count and unique identifiers")
    coordinates = {c["id"]: c for c in candidates["facilities"]}
    if len(coordinates) != len(candidates["facilities"]) or coordinates.keys() - {r["id"] for r in records}:
        raise ValueError("Duplicate or orphan medical coordinate candidates")
    facilities, excluded = [], []
    for record in records:
        if any(not record[field].strip() for field in ("id", "name", "address", "source_address", "source_form_text")):
            raise ValueError("Medical source identity, address and care form must be present")
        page = record["source_page"]
        if type(page) is not int or not 1 <= page <= source["pdf_pages"] or record["table"] != "2":
            raise ValueError("Medical source page or table differs from the reviewed PDF")
        forms = care_forms(record["source_form_text"])
        if not forms:
            excluded.append({"id": record["id"], "source_page": page, "reason": "planned_cardiology_only"})
        candidate = coordinates.get(record["id"])
        geometry = {"latitude": None, "longitude": None, "coordinate_source": None, "coordinate_status": "missing"}
        if candidate:
            validate_candidate(candidate)
            if normalized(candidate["address"]) != normalized(record["address"]):
                raise ValueError("Preserved medical coordinates belong to another address")
            geometry = {key: candidate[key] for key in geometry}
        for form in forms:
            facilities.append({
                "id": record["id"], "service": form, "name": record["name"], "address": record["address"],
                "source_url": SOURCE_URL + "#page=" + str(page), "observed_at": source["observed_at"],
                "published_on": None, "source_sha256": source["pdf_sha256"],
                "coordinate_snapshot_sha256": candidate.get("coordinate_snapshot_sha256") if candidate else None,
                "coordinate_snapshot_url": candidate.get("coordinate_snapshot_url") if candidate else None, **geometry,
            })
    return facilities, excluded


def validate_candidate(candidate: dict) -> None:
    date.fromisoformat(candidate["observed_at"])
    if candidate["coordinate_status"] == "geocoded_building":
        validate_osm_candidate(candidate)
    elif candidate["coordinate_status"] != "official_institution_pin" or not candidate["coordinate_source"].startswith("https://"):
        raise ValueError("Only original sourced institution coordinates may be preserved")
    for field, limit in (("latitude", 90), ("longitude", 180)):
        value = candidate[field]
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or abs(value) > limit:
            raise ValueError("Invalid preserved medical coordinates")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, default=Path("datasets/normative-medical-source-records.json"))
    parser.add_argument("--coordinates", type=Path, default=Path("datasets/normative-medical-coordinate-candidates.json"))
    parser.add_argument("--osm", type=Path, default=Path("datasets/normative-medical-osm-candidates.json"))
    parser.add_argument("--pbf", type=Path, default=Path(".local/normative-inputs/kurgan.osm.pbf"))
    parser.add_argument("--pdf", type=Path, default=Path(".local/research/medical-routing-1169.pdf"))
    parser.add_argument("--output", type=Path, default=Path("datasets/normative/medical.json"))
    args = parser.parse_args()
    raw = args.source.read_bytes()
    source = json.loads(raw)
    osm = json.loads(args.osm.read_bytes())
    coordinates = merge_coordinates(source, json.loads(args.coordinates.read_bytes()), osm, args.pbf.read_bytes())
    facilities, excluded = directory_facilities(source, coordinates, args.pdf.read_bytes())
    result = {
        "source_date": source["act_date"], "source_act": source["act"], "source_url": source["source_url"],
        "source_sha256": source["pdf_sha256"], "source_bytes": source["pdf_bytes"],
        "observed_at": source["observed_at"], "complete_inventory": False,
        "coordinate_extract_sha256": osm["pbf_sha256"], "coordinate_licence": osm["coordinate_licence"],
        "osm_candidates_sha256": hashlib.sha256(args.osm.read_bytes()).hexdigest(),
        "population_group": "adults_attached", "snapshot_kind": source["snapshot_kind"],
        "extracted_fields_sha256": hashlib.sha256(raw).hexdigest(),
        "profile_evidence": {"act": source["act"], "date": source["act_date"], "table": "2",
                             "pdf_pages": [10, 11, 12, 13, 14], "verified_at": source["observed_at"],
                             "source_sha256": source["pdf_sha256"], "source_bytes": source["pdf_bytes"]},
        "reviewed_address_count": len(source["records"]), "excluded_records": excluded,
        "facilities": facilities,
    }
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(len(source["records"]), len(facilities), sum(f["latitude"] is not None for f in facilities))


if __name__ == "__main__":
    main()
