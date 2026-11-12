import argparse
import hashlib
import json
from pathlib import Path

import osmium
from normative_library_matching import library_address_matches


def candidates(pbf: Path) -> list[dict]:
    result = []
    for obj in osmium.FileProcessor(str(pbf)).with_locations():
        if obj.tags.get("amenity") != "library":
            continue
        if obj.is_node():
            lon, lat = obj.lon, obj.lat
            kind = "node"
        elif obj.is_way():
            if not obj.tags.get("building") or obj.tags.get("building") == "no":
                continue
            points = [(node.lon, node.lat) for node in obj.nodes]
            if points and points[0] == points[-1]:
                points.pop()
            if not points:
                continue
            lon = sum(point[0] for point in points) / len(points)
            lat = sum(point[1] for point in points) / len(points)
            kind = "way"
        else:
            continue
        result.append(
            {"id": obj.id, "kind": kind, "tags": dict(obj.tags), "latitude": lat, "longitude": lon}
        )
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pbf", type=Path, required=True)
    parser.add_argument(
        "--dataset", type=Path, default=Path("datasets/normative/regional-libraries.json")
    )
    args = parser.parse_args()
    dataset = json.loads(args.dataset.read_text())
    objects = candidates(args.pbf)
    matches = []
    ambiguous = []
    for facility in dataset["facilities"]:
        facility.update(
            latitude=None, longitude=None, coordinate_source=None, coordinate_status="missing"
        )
        selected = [
            row for row in objects if library_address_matches(facility["address"], row["tags"])
        ]
        if len(selected) > 1:
            ambiguous.append(
                {
                    "facility_id": facility["id"],
                    "candidates": [f"{r['kind']}/{r['id']}" for r in selected],
                }
            )
        if len(selected) != 1:
            continue
        row = selected[0]
        facility.update(
            latitude=row["latitude"],
            longitude=row["longitude"],
            coordinate_source=f"https://www.openstreetmap.org/{row['kind']}/{row['id']}",
            coordinate_status="osm_institution_pin"
            if row["kind"] == "node"
            else "geocoded_building",
        )
        matches.append(
            {
                "facility_id": facility["id"],
                "osm_kind": row["kind"],
                "osm_id": row["id"],
                "matched_tags": row["tags"],
            }
        )
    dataset.update(
        coordinate_extract_url="https://download.openstreetmap.fr/extracts/russia/ural_federal_district/kurgan_oblast-latest.osm.pbf",
        coordinate_extract_sha256=hashlib.sha256(args.pbf.read_bytes()).hexdigest(),
        coordinate_licence="ODbL-1.0",
        coordinate_matches=matches,
        coordinate_ambiguous=ambiguous,
    )
    args.dataset.write_text(json.dumps(dataset, ensure_ascii=False, indent=2) + "\n")
    print("library address matches", len(matches), "ambiguous", len(ambiguous))


if __name__ == "__main__":
    main()
