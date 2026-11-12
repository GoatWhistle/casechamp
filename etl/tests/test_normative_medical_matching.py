import hashlib
from copy import deepcopy

import pytest
from normative_medical_matching import address_match, merge_coordinates, select_candidates


def building() -> dict:
    return {"id": 42, "kind": "way", "latitude": 55, "longitude": 65,
            "tags": {"addr:city": "Кетово", "addr:street": "улица Космонавтов",
                     "addr:housenumber": "48", "building": "hospital"}}


def record() -> dict:
    return {"id": "hospital", "name": "Hospital", "address": "Кетово, Космонавтов, 48"}


@pytest.mark.parametrize("changes", [
    {"addr:city": "Курган"}, {"addr:city": ""}, {"addr:housenumber": "48а"},
    {"addr:street": "переулок Космонавтов"}, {"addr:street": "улица Матросова"},
])
def test_city_street_type_and_exact_house_are_required(changes: dict) -> None:
    assert not address_match(record()["address"], {**building()["tags"], **changes})


def test_street_position_does_not_change_type_or_named_square() -> None:
    assert address_match(record()["address"], {**building()["tags"], "addr:street": "Космонавтов улица"})
    assert address_match("Макушино, Красная Площадь, 2", {
        "addr:city": "Макушино", "addr:street": "улица Красная Площадь", "addr:housenumber": "2",
    })


def test_duplicate_address_including_bank_remains_ambiguous() -> None:
    first = building()
    second = {**first, "id": 43, "tags": {**first["tags"], "amenity": "bank"}}
    selected, review = select_candidates([record()], [first, second], set())
    assert selected == []
    assert review[0]["status"] == "ambiguous"
    assert review[0]["candidate_ids"] == ["way/42", "way/43"]


def test_unique_address_preserves_original_coordinates_and_is_not_an_entrance() -> None:
    selected, review = select_candidates([record()], [building()], set())
    assert selected[0]["coordinate_status"] == "geocoded_building"
    assert selected[0]["coordinate_source"] == "https://www.openstreetmap.org/way/42"
    assert review[0]["status"] == "unique_address"
    assert select_candidates([record()], [building()], {"hospital"}) == ([], [])


@pytest.mark.parametrize("case", ["source", "override", "duplicate", "tags", "status"])
def test_unbound_source_and_candidate_promotions_are_rejected(case: str) -> None:
    pdf = b"isolated source extract"
    selected, _ = select_candidates([record()], [building()], set())
    osm = {"snapshot_kind": "exact_osm_building_addresses", "pbf_sha256": hashlib.sha256(pdf).hexdigest(),
           "observed_at": "2026-11-12", "coordinate_extract_url": "https://example.org/source.osm.pbf", "facilities": selected}
    preserved = {"facilities": []}
    if case == "source":
        pdf += b"changed"
    elif case == "override":
        preserved["facilities"] = [{"id": "hospital"}]
    elif case == "duplicate":
        osm["facilities"].append(deepcopy(selected[0]))
    elif case == "tags":
        selected[0]["matched_tags"]["addr:city"] = "Other city"
    else:
        selected[0]["coordinate_status"] = "verified_medical_entrance"
    with pytest.raises(ValueError):
        merge_coordinates({"records": [record()]}, preserved, osm, pdf)
