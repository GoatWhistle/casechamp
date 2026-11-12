from synthetic_traffic.municipal_tags import municipal_source_confirmed


def region_assignment(polygon, tags, regions, region_polygons, tree, city_only=False):
    overlaps = [
        (
            float(
                polygon.intersection(region_polygons[int(index)]).area / polygon.area
            ),
            int(index),
        )
        for index in tree.query(polygon)
    ]
    fraction, index = max(overlaps, default=(0, -1))
    if fraction >= 0.90:
        return fraction, index, "maximum_supplied_region_polygon_overlap"
    confirmed_city = (
        city_only
        and index >= 0
        and regions[index]["id"] == "40000000"
        and tags.get("admin_level") == "8"
        and tags.get("addr:region") == regions[index]["name"] == "Санкт-Петербург"
        and municipal_source_confirmed(tags)
        and fraction >= 0.80
        and region_polygons[index].covers(polygon.representative_point())
    )
    return (
        fraction,
        index,
        "source_confirmed_city_assignment" if confirmed_city else None,
    )
