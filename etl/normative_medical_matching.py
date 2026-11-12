import math
import hashlib
from datetime import date
import re

from normative_address import normalized


STREET_TYPES = ("улица", "переулок", "проспект", "тракт", "проезд", "площадь")


def street_key(value: str, canonical: bool = False) -> tuple[str, str]:
    text = " ".join(value.casefold().split())
    for kind in STREET_TYPES:
        if text.startswith(kind + " "):
            return kind, normalized(text[len(kind):])
        if text.endswith(" " + kind) and (not canonical or kind == "тракт"):
            return kind, normalized(text[:-len(kind)])
    return "улица", normalized(text)


def address_match(address: str, tags: dict) -> bool:
    parts = [part.strip() for part in address.split(",")]
    if len(parts) != 3:
        return False
    city, street, house = parts
    if not all(tags.get(key) for key in ("addr:city", "addr:street", "addr:housenumber")):
        return False
    if normalized(city) != normalized(tags["addr:city"]) or normalized(house) != normalized(tags["addr:housenumber"]):
        return False
    return street_key(street, canonical=True) == street_key(tags["addr:street"])


def select_candidates(records: list[dict], objects: list[dict], preserved: set[str]) -> tuple[list[dict], list[dict]]:
    selected, review = [], []
    for record in records:
        if record["id"] in preserved:
            continue
        matches = [obj for obj in objects if address_match(record["address"], obj["tags"])]
        review.append({"id": record["id"], "candidate_ids": [f"{r['kind']}/{r['id']}" for r in matches],
                       "status": "unique_address" if len(matches) == 1 else "ambiguous" if matches else "unmatched"})
        if len(matches) != 1:
            continue
        obj = matches[0]
        if obj["kind"] != "way" or not obj["tags"].get("building") or obj["tags"]["building"] == "no":
            continue
        if obj["tags"].get("amenity") not in (None, "hospital", "clinic", "doctors"):
            continue
        for key, limit in (("latitude", 90), ("longitude", 180)):
            value = obj[key]
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or abs(value) > limit:
                raise ValueError("Medical OSM candidates require finite coordinates")
        selected.append({"id": record["id"], "name": record["name"], "address": record["address"],
                         "latitude": obj["latitude"], "longitude": obj["longitude"],
                         "coordinate_source": f"https://www.openstreetmap.org/way/{obj['id']}",
                         "coordinate_status": "geocoded_building", "matched_tags": obj["tags"]})
    return selected, review


def validate_osm_candidate(candidate: dict) -> None:
    if candidate["coordinate_status"] != "geocoded_building":
        raise ValueError("OSM medical buildings do not establish verified entrances")
    if not re.fullmatch(r"https://www\.openstreetmap\.org/way/[0-9]+", candidate["coordinate_source"]):
        raise ValueError("Medical building coordinates require their exact OSM way")
    if not address_match(candidate["address"], candidate["matched_tags"]):
        raise ValueError("Medical building address does not match its OSM tags")


def merge_coordinates(source: dict, preserved: dict, osm: dict, pbf: bytes) -> dict:
    if osm.get("snapshot_kind") != "exact_osm_building_addresses" or hashlib.sha256(pbf).hexdigest() != osm["pbf_sha256"]:
        raise ValueError("Medical OSM coordinates require the exact source extract")
    date.fromisoformat(osm["observed_at"])
    records = {r["id"]: r for r in source["records"]}
    candidates = list(preserved["facilities"])
    known = {r["id"] for r in candidates}
    for candidate in osm["facilities"]:
        if candidate["id"] in known or candidate["id"] not in records:
            raise ValueError("Medical OSM candidates cannot replace or invent institutions")
        if candidate["address"] != records[candidate["id"]]["address"]:
            raise ValueError("Medical OSM candidates require the reviewed primary address")
        validate_osm_candidate(candidate)
        candidates.append({**candidate, "observed_at": osm["observed_at"],
                           "coordinate_snapshot_sha256": osm["pbf_sha256"],
                           "coordinate_snapshot_url": osm["coordinate_extract_url"]})
        known.add(candidate["id"])
    return {**preserved, "facilities": candidates}
