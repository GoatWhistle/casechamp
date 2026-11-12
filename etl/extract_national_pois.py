import argparse
import gzip
import hashlib
import json
from collections import Counter
from pathlib import Path

import osmium
from shapely import STRtree, make_valid
from shapely.geometry import MultiPolygon, Point

from national_poi_categories import categories


class RegionIndex:
    def __init__(self, records: list[dict]) -> None:
        self.regions = records
        geometries = [make_valid(MultiPolygon([(rings[0], rings[1:]) for rings in r["polygons"] if rings])) for r in records]
        self.tree = STRtree(geometries)

    def locate(self, lat: float, lon: float) -> tuple[str | None, str | None, str]:
        matches = self.tree.query(Point(lon, lat), predicate="intersects")
        if len(matches) != 1:
            return None, None, "ambiguous" if len(matches) else "outside"
        region = self.regions[int(matches[0])]
        return region["id"], region["name"], "spatial_match"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--district", required=True)
    parser.add_argument("--root", type=Path, default=Path(".local/normative-national-inputs"))
    args = parser.parse_args()
    manifest = json.loads((args.root / "osm/manifest.json").read_text())
    source = next(row for row in manifest if row["id"] == args.district)
    pbf = args.root / "osm" / (args.district + ".osm.pbf")
    digest = hashlib.sha256()
    with pbf.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    if digest.hexdigest() != source["sha256"] or pbf.stat().st_size != source["bytes"]:
        raise ValueError("National extract differs from its acquisition manifest")
    boundary_bytes = (args.root / "regions.json").read_bytes()
    index = RegionIndex(json.loads(boundary_bytes)["regions"])
    output = args.root / "derived"
    output.mkdir(exist_ok=True)
    path = output / (args.district + ".pois.jsonl.gz")
    counts, regional, matches = Counter(), Counter(), Counter()
    filters = osmium.filter.TagFilter(*[("amenity", value) for value in ("school", "library", "fire_station", "bus_station", "hospital", "clinic")],
                                     ("healthcare", "hospital"), ("healthcare", "clinic"), ("highway", "bus_stop"),
                                     ("public_transport", "platform"), ("office", "employment_agency"), ("office", "government"), ("office", "mfc"))
    processor = osmium.FileProcessor(str(pbf)).with_locations().with_filter(filters)
    with gzip.open(path.with_suffix(".gz.part"), "wt", encoding="utf-8") as target:
        for obj in processor:
            tags = dict(obj.tags)
            groups = categories(tags)
            if not groups:
                continue
            if obj.is_node() and obj.location.valid():
                lat, lon, method, kind = obj.lat, obj.lon, "osm_node", "node"
            elif obj.is_way() and len(obj.nodes) >= 4 and obj.nodes[0].ref == obj.nodes[-1].ref and all(n.location.valid() for n in obj.nodes):
                points = [(n.lat, n.lon) for n in obj.nodes][:-1]
                lat, lon = sum(p[0] for p in points) / len(points), sum(p[1] for p in points) / len(points)
                method, kind = "closed_way_vertex_mean", "way"
            else:
                matches["geometry_missing"] += 1
                continue
            region_id, region_name, assignment = index.locate(lat, lon)
            matches[assignment] += 1
            record = {"id": f"osm-{kind}-{obj.id}", "osm_kind": kind, "osm_id": obj.id, "osm_version": obj.version,
                      "name": tags.get("name"), "categories": groups, "tags": tags,
                      "latitude": lat, "longitude": lon, "geometry_method": method,
                      "region_id": region_id, "region_name": region_name, "region_assignment": assignment,
                      "source_url": f"https://www.openstreetmap.org/{kind}/{obj.id}",
                      "source_sha256": source["sha256"], "snapshot_url": source["url"], "observed_at": source["received_at"],
                      "operational_status": "unconfirmed", "profile_verification": "unconfirmed"}
            target.write(json.dumps(record, ensure_ascii=False) + "\n")
            counts.update(groups)
            if region_id:
                regional[region_id] += 1
    path.with_suffix(".gz.part").replace(path)
    summary = {"district": args.district, "source": source, "boundary_sha256": hashlib.sha256(boundary_bytes).hexdigest(),
               "categories": dict(counts), "regions": dict(regional), "assignment": dict(matches),
               "rows": sum(matches[k] for k in ("spatial_match", "ambiguous", "outside")), "objects_are_not_unique_institutions": True}
    path.with_suffix(".summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
