import json
from pathlib import Path

from analytics.client import ClickHouse
from app.domain.normative.model import Facility
from app.domain.normative.fire_destination import FireDestination
from app.domain.normative.territory import TerritoryContext
from app.domain.normative.fire_evidence.facts import FireFacts
from app.domain.normative.library.facts import LibraryFacts
from app.domain.normative.medical.facts import MedicalFacts
from app.domain.normative.walking_facts import WalkingFacts

ROOT = Path(__file__).resolve().parent.parent


def walking_fact(record: dict) -> WalkingFacts:
    normalized = dict(record)
    for field in ("zones", "eligible_facility_ids", "verified_closed_way_ids"):
        value = record.get(field, [])
        if not isinstance(value, (list, tuple)):
            raise TypeError(f"Walking fact {field} must be an array")
        normalized[field] = tuple(value)
    return WalkingFacts(**normalized)


def library_fact(record: dict) -> LibraryFacts:
    normalized = dict(record)
    for field in ("eligible_facility_ids", "verified_closed_way_ids"):
        value = record.get(field, [])
        if not isinstance(value, (list, tuple)):
            raise TypeError(f"Library fact {field} must be an array")
        normalized[field] = tuple(value)
    return LibraryFacts(**normalized)


def medical_fact(record: dict) -> MedicalFacts:
    normalized = dict(record)
    for field in ("eligible_facility_ids", "verified_closed_way_ids"):
        value = record.get(field, [])
        if not isinstance(value, (list, tuple)):
            raise TypeError(f"Medical fact {field} must be an array")
        normalized[field] = tuple(value)
    return MedicalFacts(**normalized)


def fire_fact(record: dict) -> FireFacts:
    normalized = dict(record)
    for field in ("eligible_facility_ids", "verified_closed_way_ids"):
        value = record.get(field, [])
        if not isinstance(value, (list, tuple)):
            raise TypeError(f"Fire fact {field} must be an array")
        normalized[field] = tuple(value)
    return FireFacts(**normalized)


def main() -> None:
    criteria = json.loads((ROOT / "datasets/normative/criteria.json").read_text())
    sources = sorted(path for path in (ROOT / "datasets/normative").glob("*.json")
                     if path.name != "criteria.json")
    facilities = [
        f for source in sources for f in json.loads(source.read_text())["facilities"]
    ]
    for record in facilities:
        Facility(**record)
    if len({c["id"] for c in criteria}) != len(criteria):
        raise ValueError("Duplicate criteria")
    if len({(f["id"], f["service"]) for f in facilities}) != len(facilities):
        raise ValueError("Duplicate facilities")
    territories = json.loads((ROOT / "datasets/normative-territories.json").read_text())["territories"]
    parsed_territories = [TerritoryContext(**record) for record in territories]
    if len({record.point_id for record in parsed_territories}) != len(parsed_territories):
        raise ValueError("Duplicate territorial evidence")
    settlement_types = json.loads((ROOT / "datasets/normative-settlements.json").read_text())["settlements"]
    walking_facts = json.loads((ROOT / "datasets/normative-walking-facts.json").read_text())["facts"]
    parsed = [walking_fact(row) for row in walking_facts]
    if len({(row.service, row.origin_id) for row in parsed}) != len(parsed):
        raise ValueError("Duplicate walking facts")
    library_facts = json.loads((ROOT / "datasets/normative-library-facts.json").read_text())["facts"]
    parsed_library = [library_fact(row) for row in library_facts]
    if len({row.origin_id for row in parsed_library}) != len(parsed_library):
        raise ValueError("Duplicate library evidence")
    medical_facts = json.loads((ROOT / "datasets/normative-medical-facts.json").read_text())["facts"]
    parsed_medical = [medical_fact(row) for row in medical_facts]
    if len({(row.service, row.origin_id) for row in parsed_medical}) != len(parsed_medical):
        raise ValueError("Duplicate medical evidence")
    fire_facts = json.loads((ROOT / "datasets/normative-fire-facts.json").read_text())["facts"]
    parsed_fire = [fire_fact(row) for row in fire_facts]
    if len({row.origin_id for row in parsed_fire}) != len(parsed_fire):
        raise ValueError("Duplicate fire evidence")
    destinations = json.loads((ROOT / "datasets/normative-fire-destinations.json").read_text())["destinations"]
    parsed_destinations = [FireDestination(**row) for row in destinations]
    if len({d.id for d in parsed_destinations}) != len(parsed_destinations):
        raise ValueError("Duplicate fire destination identifiers")
    client = ClickHouse()
    for filename in ("normative.sql", "normative-fire.sql"):
        for statement in (ROOT / "infra/clickhouse" / filename).read_text().split(";"):
            if statement.strip():
                client.request(statement)
    for table, records in [("criteria", criteria), ("facilities", facilities), ("territories", territories), ("settlement_types", settlement_types), ("walking_facts", walking_facts), ("library_facts", library_facts), ("medical_facts", medical_facts), ("fire_facts", fire_facts), ("fire_destinations", destinations)]:
        client.request(f"TRUNCATE TABLE plexus_normative.{table}")
        if not records:
            print(table, 0)
            continue
        payload = "\n".join(json.dumps(r, ensure_ascii=False) for r in records).encode()
        client.request(
            f"INSERT INTO plexus_normative.{table} FORMAT JSONEachRow", payload
        )
        print(table, len(records))


if __name__ == "__main__":
    main()
