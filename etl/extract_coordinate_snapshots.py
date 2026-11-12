import argparse
import hashlib
import json
import re
from pathlib import Path

import osmium


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pbf", type=Path, default=Path(".local/normative-inputs/kurgan.osm.pbf"))
    parser.add_argument("--output", type=Path, default=Path("datasets/normative-coordinate-snapshot-records.json"))
    args = parser.parse_args()
    wanted = set()
    for path in Path("datasets/normative").glob("*.json"):
        if path.name == "criteria.json":
            continue
        for row in json.loads(path.read_text())["facilities"]:
            match = re.fullmatch(r"https://www\.openstreetmap\.org/(node|way)/([0-9]+)", row.get("coordinate_source") or "")
            if match:
                wanted.add((match[1], int(match[2])))
    records = []
    for obj in osmium.FileProcessor(str(args.pbf)).with_locations():
        kind = "node" if obj.is_node() else "way" if obj.is_way() else None
        if (kind, obj.id) not in wanted:
            continue
        if kind == "node":
            if not obj.location.valid():
                continue
            lat, lon, method = obj.lat, obj.lon, "osm_node"
            box = {"latitude": lat, "longitude": lon}
            centroid = box
        else:
            if len(obj.nodes) < 4 or obj.nodes[0].ref != obj.nodes[-1].ref or any(not n.location.valid() for n in obj.nodes):
                continue
            points = [(n.lat, n.lon) for n in obj.nodes][:-1]
            lat, lon = sum(p[0] for p in points) / len(points), sum(p[1] for p in points) / len(points)
            method = "closed_way_vertex_mean"
            box = {"latitude": (min(p[0] for p in points) + max(p[0] for p in points)) / 2,
                   "longitude": (min(p[1] for p in points) + max(p[1] for p in points)) / 2}
            shifted = [(x - points[0][1], y - points[0][0]) for y, x in points]
            pairs = list(zip(shifted, shifted[1:] + shifted[:1]))
            cross = [a[0] * b[1] - b[0] * a[1] for a, b in pairs]
            area = sum(cross)
            centroid = {"latitude": sum((a[1] + b[1]) * c for (a, b), c in zip(pairs, cross)) / (3 * area) + points[0][0],
                        "longitude": sum((a[0] + b[0]) * c for (a, b), c in zip(pairs, cross)) / (3 * area) + points[0][1]} if area else box
        records.append({"kind": kind, "id": obj.id, "version": obj.version, "timestamp": str(obj.timestamp),
                        "latitude": lat, "longitude": lon, "geometry_method": method, "bounding_box_center": box, "area_centroid": centroid})
    args.output.write_text(json.dumps({"pbf_sha256": hashlib.sha256(args.pbf.read_bytes()).hexdigest(),
                                     "coordinate_licence": "ODbL-1.0", "records": records}, ensure_ascii=False, indent=2) + "\n")
    print("requested", len(wanted), "extracted", len(records))


if __name__ == "__main__":
    main()
