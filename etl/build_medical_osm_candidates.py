import argparse
import hashlib
import json
from pathlib import Path

import osmium

from normative_medical_matching import select_candidates


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pbf", type=Path, default=Path(".local/normative-inputs/kurgan.osm.pbf"))
    parser.add_argument("--output", type=Path, default=Path("datasets/normative-medical-osm-candidates.json"))
    args = parser.parse_args()
    source = json.loads(Path("datasets/normative-medical-source-records.json").read_text())
    preserved = json.loads(Path("datasets/normative-medical-coordinate-candidates.json").read_text())
    objects = []
    for obj in osmium.FileProcessor(str(args.pbf)).with_locations():
        if not obj.is_way() or not obj.tags.get("building") or obj.tags.get("building") == "no":
            continue
        tags = dict(obj.tags)
        if not all(tags.get(key) for key in ("addr:city", "addr:street", "addr:housenumber")):
            continue
        if len(obj.nodes) < 4 or obj.nodes[0].ref != obj.nodes[-1].ref or any(not n.location.valid() for n in obj.nodes):
            continue
        points = [(node.lat, node.lon) for node in list(obj.nodes)[:-1]]
        objects.append({"id": obj.id, "kind": "way", "tags": tags,
                        "latitude": sum(p[0] for p in points) / len(points),
                        "longitude": sum(p[1] for p in points) / len(points)})
    selected, review = select_candidates(source["records"], objects, {r["id"] for r in preserved["facilities"]})
    result = {"snapshot_kind": "exact_osm_building_addresses", "observed_at": source["observed_at"],
              "coordinate_extract_url": "https://download.openstreetmap.fr/extracts/russia/ural_federal_district/kurgan_oblast-latest.osm.pbf",
              "pbf_sha256": hashlib.sha256(args.pbf.read_bytes()).hexdigest(),
              "coordinate_licence": "ODbL-1.0", "geometry_method": "closed_way_vertex_mean",
              "facilities": selected, "address_review": review}
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print("matched", len(selected), "reviewed", len(review))


if __name__ == "__main__":
    main()
