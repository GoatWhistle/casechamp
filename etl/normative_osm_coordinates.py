import argparse
import hashlib
import json
import re
from pathlib import Path

import osmium


def tokens(value: str) -> str:
    return " ".join(re.findall(r"[а-яё0-9]+", value.lower()))


def matches(address: str, tags: dict[str, str]) -> bool:
    city = tokens(tags.get("addr:city", ""))
    street = tokens(tags.get("addr:street", ""))
    house = tokens(tags.get("addr:housenumber", ""))
    cleaned = tokens(address)
    return bool(city and street and house and city in cleaned and street in cleaned
                and re.search(r"(?:^| )" + re.escape(house) + r"$", cleaned))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pbf", type=Path, required=True)
    args = parser.parse_args()
    path = Path("datasets/normative/bus-stations.json")
    dataset = json.loads(path.read_text())
    candidates = []
    for obj in osmium.FileProcessor(str(args.pbf)).with_locations():
        if not obj.is_way() or obj.tags.get("amenity") != "bus_station":
            continue
        if obj.tags.get("building") not in ("yes", "transportation", "public"):
            continue
        coordinates = [(node.lon, node.lat) for node in obj.nodes]
        if coordinates[0] == coordinates[-1]:
            coordinates.pop()
        candidates.append({"id": obj.id, "tags": dict(obj.tags),
                           "latitude": sum(c[1] for c in coordinates) / len(coordinates),
                           "longitude": sum(c[0] for c in coordinates) / len(coordinates)})
    matched = []
    for facility in dataset["facilities"]:
        found = [row for row in candidates if matches(facility["address"], row["tags"])]
        if len(found) != 1:
            continue
        row = found[0]
        facility.update(latitude=row["latitude"], longitude=row["longitude"],
                        coordinate_source=f"https://www.openstreetmap.org/way/{row['id']}",
                        coordinate_status="geocoded_building")
        matched.append({"facility_id": facility["id"], "osm_way": row["id"],
                        "matched_tags": row["tags"]})
    dataset.update(coordinate_extract_url="https://download.openstreetmap.fr/extracts/russia/ural_federal_district/kurgan_oblast-latest.osm.pbf",
                   coordinate_extract_sha256=hashlib.sha256(args.pbf.read_bytes()).hexdigest(),
                   coordinate_licence="ODbL-1.0", coordinate_matches=matched)
    path.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n")
    print("bus-station address matches", len(matched))


if __name__ == "__main__":
    main()
