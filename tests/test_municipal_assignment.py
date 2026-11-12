import pytest
from shapely.geometry import box
from shapely.strtree import STRtree
from synthetic_traffic.municipal_assignment import region_assignment


def assign(source, region, tags, city_only=True):
    return region_assignment(
        source,
        tags,
        [{"id": "40000000", "name": "Санкт-Петербург"}],
        [region],
        STRtree([region]),
        city_only,
    )


def test_city_assignment_preserves_full_source_polygon_and_actual_overlap():
    source = box(0, 0, 1, 1)
    before = source.wkb
    tags = {
        "admin_level": "8",
        "addr:region": "Санкт-Петербург",
        "official_name": "муниципальный округ",
    }
    fraction, index, basis = assign(source, box(0.2, 0, 1, 1), tags)
    assert fraction == pytest.approx(0.8)
    assert index == 0
    assert basis == "source_confirmed_city_assignment"
    assert source.wkb == before
    assert assign(source, box(0.2, 0, 1, 1), tags, False)[2] is None


def test_city_override_rejects_conflicting_affiliation_missing_evidence_and_outside_point():
    source = box(0, 0, 1, 1)
    region = box(0.2, 0, 1, 1)
    tags = {
        "admin_level": "8",
        "addr:region": "Санкт-Петербург",
        "official_name": "муниципальный округ",
    }
    assert assign(source, region, {**tags, "addr:region": "another region"})[2] is None
    assert (
        assign(source, region, {"admin_level": "8", "addr:region": "Санкт-Петербург"})[
            2
        ]
        is None
    )
    assert assign(source, region, {**tags, "admin_level": "6"})[2] is None
    assert assign(source, box(2, 2, 3, 3), tags)[2] is None
    split_region = box(0, 0, 0.4, 1).union(box(0.6, 0, 1, 1))
    assert assign(source, split_region, tags)[2] is None
