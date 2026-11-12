from synthetic_traffic.municipal_fallback import prepare_historical_districts


def test_historical_geometry_only_fills_missing_regions_and_keeps_source_year():
    ring = [[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]
    regions = [
        {"id": "known", "polygons": [[ring]]},
        {"id": "missing", "polygons": [[[[x + 2, y] for x, y in ring]]]},
    ]
    features = [
        {
            "type": "Feature",
            "properties": {"shapeID": identifier, "shapeName": identifier},
            "geometry": {
                "type": "Polygon",
                "coordinates": [[[x + offset, y] for x, y in ring]],
            },
        }
        for identifier, offset in [("a", 0), ("b", 2)]
    ]
    accepted, rejected = prepare_historical_districts(
        {"features": features}, regions, {"known"}, "sourcehash"
    )
    assert rejected == []
    assert len(accepted) == 1
    assert accepted[0]["properties"]["region_id"] == "missing"
    assert accepted[0]["properties"]["observed_at"] == "2017"
    assert accepted[0]["properties"]["admin_level"] == 0
    assert accepted[0]["properties"]["osm_relation_id"] == 0
    assert accepted[0]["geometry"]["type"] == "MultiPolygon"
