import pytest
from synthetic_traffic.municipal_import import prepare_import


def feature(year="2017"):
    return {
        "geometry": {
            "type": "MultiPolygon",
            "coordinates": [[[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]]],
        },
        "properties": {
            "id": "same",
            "region_id": "region",
            "name": "District",
            "admin_level": 0,
            "osm_relation_id": 0,
            "source_url": "https://example.org/source",
            "observed_at": year,
            "source_sha256": "hash",
            "region_assignment": "original",
            "region_overlap_fraction": 1,
        },
    }


def test_existing_newer_snapshot_is_preserved():
    old = {
        "same": {
            "region_id": "region",
            "observed_at": "2026-11-11",
            "source_sha256": "current",
        }
    }
    records, skipped = prepare_import([feature()], old, 1)
    assert records == []
    assert skipped == 1
    assert old["same"]["source_sha256"] == "current"


def test_repeat_import_is_idempotent_and_region_change_rejected():
    existing = {}
    records, skipped = prepare_import([feature(), feature()], existing, 1)
    assert len(records) == 1
    assert skipped == 1
    existing["same"]["region_id"] = "another"
    with pytest.raises(ValueError, match="changed region"):
        prepare_import([feature("2026")], existing, 2)
