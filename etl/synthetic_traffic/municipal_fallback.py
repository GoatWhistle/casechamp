from shapely import make_valid
from shapely.geometry import MultiPolygon, mapping, shape
from shapely.strtree import STRtree


def prepare_historical_districts(document, regions, excluded_regions, source_sha256):
    polygons = [
        make_valid(shape({"type": "MultiPolygon", "coordinates": row["polygons"]}))
        for row in regions
    ]
    tree = STRtree(polygons)
    accepted, rejected = [], []
    for feature in document["features"]:
        geometry = shape(feature["geometry"])
        identifier = feature["properties"]["shapeID"]
        if (
            geometry.geom_type not in {"Polygon", "MultiPolygon"}
            or geometry.is_empty
            or not geometry.is_valid
        ):
            rejected.append(
                {"id": identifier, "reason": "invalid_original_source_geometry"}
            )
            continue
        overlaps = [
            (
                float(geometry.intersection(polygons[int(index)]).area / geometry.area),
                int(index),
            )
            for index in tree.query(geometry)
        ]
        fraction, index = max(overlaps, default=(0, -1))
        if fraction < 0.90:
            rejected.append(
                {
                    "id": identifier,
                    "reason": "region_overlap_below_90_percent",
                    "fraction": fraction,
                }
            )
            continue
        region = regions[index]["id"]
        if region in excluded_regions:
            continue
        if geometry.geom_type == "Polygon":
            geometry = MultiPolygon([geometry])
        accepted.append(
            {
                "type": "Feature",
                "geometry": mapping(geometry),
                "properties": {
                    "id": "geoboundaries-2017-" + identifier,
                    "region_id": region,
                    "name": feature["properties"]["shapeName"],
                    "admin_level": 0,
                    "osm_relation_id": 0,
                    "source_url": "https://www.geoboundaries.org/api/current/gbOpen/RUS/ADM2/",
                    "observed_at": "2017",
                    "source_sha256": source_sha256,
                    "region_assignment": "historical_ADM2_Raion_2017_maximum_supplied_region_polygon_overlap",
                    "region_overlap_fraction": fraction,
                    "bounds": list(geometry.bounds),
                },
            }
        )
    return accepted, rejected
