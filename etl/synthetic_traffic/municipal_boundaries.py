import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

import osmium
from shapely import from_wkb, make_valid
from shapely.geometry import MultiPolygon, mapping, shape
from shapely.strtree import STRtree


def file_sha256(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class MunicipalHandler(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.factory = osmium.geom.WKBFactory()
        self.expected = {}
        self.polygons = {}
        self.invalid = []

    def relation(self, relation):
        if (
            relation.tags.get("boundary") == "administrative"
            and relation.tags.get("admin_level") == "6"
        ):
            self.expected[relation.id] = dict(relation.tags)

    def area(self, area):
        if (
            area.from_way()
            or area.tags.get("boundary") != "administrative"
            or area.tags.get("admin_level") != "6"
        ):
            return
        try:
            polygon = from_wkb(bytes.fromhex(self.factory.create_multipolygon(area)))
            if (
                polygon.is_empty
                or not polygon.is_valid
                or polygon.geom_type != "MultiPolygon"
            ):
                raise ValueError("Invalid or incomplete original polygon")
            self.polygons[area.orig_id()] = (polygon, dict(area.tags))
        except (RuntimeError, ValueError) as error:
            self.invalid.append(
                {"osm_relation_id": area.orig_id(), "reason": str(error)}
            )


def extract_municipal_boundaries(pbfs, regions_path, output):
    region_document = json.loads(Path(regions_path).read_text())
    regions = (
        region_document.get("regions", region_document)
        if isinstance(region_document, dict)
        else region_document
    )
    region_polygons = [
        MultiPolygon(
            [
                shape({"type": "Polygon", "coordinates": polygon})
                for polygon in row["polygons"]
            ]
        )
        for row in regions
    ]
    repaired_regions = [
        row["id"]
        for row, polygon in zip(regions, region_polygons, strict=True)
        if not polygon.is_valid
    ]
    region_polygons = [
        polygon if polygon.is_valid else make_valid(polygon)
        for polygon in region_polygons
    ]
    tree = STRtree(region_polygons)
    records, sources, rejected = {}, [], []
    for pbf in map(Path, pbfs):
        digest = file_sha256(pbf)
        with osmium.io.Reader(str(pbf)) as reader:
            timestamp = reader.header().get("osmosis_replication_timestamp")
        if not timestamp:
            raise ValueError("PBF requires its source snapshot timestamp")
        handler = MunicipalHandler()
        handler.apply_file(str(pbf), locations=True, idx="flex_mem")
        missing = sorted(set(handler.expected) - set(handler.polygons))
        sources.append(
            {
                "path": str(pbf),
                "sha256": digest,
                "osm_timestamp": timestamp,
                "expected_relations": len(handler.expected),
                "assembled_relations": len(handler.polygons),
                "incomplete_or_invalid_relations": missing,
                "invalid": handler.invalid,
            }
        )
        for identifier, (polygon, tags) in handler.polygons.items():
            overlaps = [
                (
                    float(
                        polygon.intersection(region_polygons[int(index)]).area
                        / polygon.area
                    ),
                    int(index),
                )
                for index in tree.query(polygon)
            ]
            fraction, index = max(overlaps, default=(0, -1))
            if fraction < 0.90 or not tags.get("name"):
                rejected.append(
                    {
                        "osm_relation_id": identifier,
                        "source_sha256": digest,
                        "reason": "region_overlap_below_90_percent_or_name_missing",
                        "maximum_overlap_fraction": fraction,
                    }
                )
                continue
            record = {
                "type": "Feature",
                "geometry": mapping(polygon),
                "properties": {
                    "id": "osm-relation-" + str(identifier),
                    "region_id": regions[index]["id"],
                    "name": tags.get("name:ru", tags["name"]),
                    "admin_level": 6,
                    "osm_relation_id": identifier,
                    "source_url": "https://www.openstreetmap.org/relation/"
                    + str(identifier),
                    "observed_at": timestamp,
                    "source_sha256": digest,
                    "region_assignment": "maximum_supplied_region_polygon_overlap",
                    "region_overlap_fraction": fraction,
                    "bounds": list(polygon.bounds),
                    "osm_tags": tags,
                },
            }
            if (
                identifier not in records
                or records[identifier]["properties"]["observed_at"] < timestamp
            ):
                records[identifier] = record
        print(
            json.dumps(
                {
                    "source": str(pbf),
                    "assembled": len(handler.polygons),
                    "missing": len(missing),
                    "accepted_total": len(records),
                }
            ),
            flush=True,
        )
    features = sorted(
        records.values(),
        key=lambda row: (row["properties"]["region_id"], row["properties"]["id"]),
    )
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(
            {"type": "FeatureCollection", "features": features},
            ensure_ascii=False,
            separators=(",", ":"),
        )
    )
    counts = {}
    for feature in features:
        region = feature["properties"]["region_id"]
        counts[region] = counts.get(region, 0) + 1
    manifest = {
        "created_at": datetime.now(UTC).isoformat(),
        "status": "partial_source_coverage",
        "method": "original_osm_assembled_admin_level_6_relations_no_invented_rings",
        "license": "ODbL-1.0; OpenStreetMap contributors",
        "sources": sources,
        "region_geometry_source": str(regions_path),
        "region_geometry_sha256": file_sha256(regions_path),
        "region_attribution_topology_repaired_ids": repaired_regions,
        "features": len(features),
        "counts_by_region": counts,
        "rejected_region_attribution": rejected,
        "missing_regions": [row["id"] for row in regions if row["id"] not in counts],
        "artifact_sha256": file_sha256(output),
        "limitation": "OSM mapped administrative districts and urban okrugs; not verified legal municipality inventory; incomplete source relations omitted; no normative index assigned",
    }
    output.with_suffix(".manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2)
    )
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--pbf", type=Path, action="append", required=True)
    parser.add_argument("--regions", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    print(
        json.dumps(
            extract_municipal_boundaries(args.pbf, args.regions, args.output),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
