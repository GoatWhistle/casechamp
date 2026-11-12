import hashlib
import json
from copy import deepcopy

import pytest
from stamp_coordinate_snapshots import geocoder_snapshot, geometry_method, stamp


def facility() -> dict:
    return {"id": "site", "service": "mfc", "name": "Office", "address": "Address",
            "source_url": "https://example.org/address", "observed_at": "2026-11-12",
            "latitude": 55, "longitude": 65, "coordinate_source": "https://example.org/geometry",
            "coordinate_status": "geocoded_building", "source_sha256": "ab" * 32}


def test_coordinate_snapshot_is_independent_idempotent_and_does_not_mutate_input() -> None:
    row = facility()
    before = deepcopy(row)
    result = stamp(row, "cd" * 32, "https://example.org/extract")
    assert row == before
    assert result["source_sha256"] == "ab" * 32
    assert result["coordinate_snapshot_sha256"] == "cd" * 32
    assert stamp(result, "cd" * 32, "https://example.org/extract") == result
    with pytest.raises(ValueError):
        stamp(result, "ef" * 32, "https://example.org/extract")


def test_cached_geocoder_must_reproduce_both_coordinates_before_hashing() -> None:
    raw = json.dumps([{"lat": "55", "lon": "65"}]).encode()
    assert geocoder_snapshot(facility(), raw) == (hashlib.sha256(raw).hexdigest(), facility()["coordinate_source"])
    for changed in (b"[]", b'[{"lat":"55","lon":"66"}]'):
        with pytest.raises(ValueError):
            geocoder_snapshot(facility(), changed)


def test_geometry_method_is_reproduced_and_only_allows_recorded_rounding() -> None:
    actual = {"latitude": 55, "longitude": 65, "geometry_method": "closed_way_vertex_mean",
              "area_centroid": {"latitude": 55.001, "longitude": 65.001}}
    assert geometry_method(facility(), actual) == "closed_way_vertex_mean"
    assert geometry_method({**facility(), "latitude": 55.001, "longitude": 65.001}, actual) == "area_centroid"
    assert geometry_method({**facility(), "latitude": 55.00000005}, actual) == "closed_way_vertex_mean"
    with pytest.raises(ValueError):
        geometry_method({**facility(), "latitude": 55.000005}, actual)
