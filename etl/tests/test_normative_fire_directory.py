from copy import deepcopy
from hashlib import sha256

import pytest
from normative_fire_directory import directory_facilities

PDF = b"%PDF-review-fixture"


def source() -> dict:
    return {
        "snapshot_kind": "reviewed_pdf_address_rows",
        "source_url": "https://45.mchs.gov.ru/directory.pdf",
        "observed_at": "2026-11-12T12:00:00Z",
        "pdf_sha256": sha256(PDF).hexdigest(),
        "pdf_bytes": len(PDF),
        "pdf_pages": 12,
        "address_rows_reviewed": 1,
        "inventory_status": "partial",
        "operational_status": "unconfirmed",
        "records": [
            {
                "id": "psch-04",
                "name": "4 ПСЧ",
                "source_address": "г. Курган, ул. Пушкина, 58",
                "address": "г. Курган, ул. Пушкина, 58",
                "source_page": 10,
                "address_status": "complete",
            }
        ],
    }


def coordinates() -> dict:
    return {
        "facilities": [
            {
                "id": "psch-04",
                "service": "fire",
                "address": "г. Курган, ул. Пушкина, 58",
                "observed_at": "2026-11-12",
                "latitude": 55,
                "longitude": 65,
                "coordinate_source": "https://www.openstreetmap.org/way/42",
                "coordinate_status": "osm_fire_building_exit_unverified",
            }
        ]
    }


def test_all_address_rows_survive_without_inventing_coordinates_or_a_publication_date() -> (
    None
):
    data = source()
    second = {
        **data["records"][0],
        "id": "psch-34",
        "name": "34 ПСЧ",
        "address_status": "house_missing",
    }
    data["records"].append(second)
    data["address_rows_reviewed"] = 2
    result, excluded = directory_facilities(data, coordinates(), PDF)
    assert len(result) == 2 and excluded == []
    assert result[0]["latitude"] == 55
    assert result[0]["coordinate_status"] == "osm_fire_building_exit_unverified"
    assert result[0]["source_url"].endswith("#page=10")
    assert result[1]["latitude"] is None and result[1]["coordinate_source"] is None
    assert all(r["published_on"] is None for r in result)


def test_conflicting_street_kind_or_house_never_inherits_coordinates() -> None:
    for address in ["г. Курган, проспект Пушкина, 58", "г. Курган, ул. Пушкина, 59"]:
        data = source()
        data["records"][0]["address"] = address
        result, excluded = directory_facilities(data, coordinates(), PDF)
        assert (
            result[0]["latitude"] is None
            and result[0]["coordinate_status"] == "address_conflict"
        )
        assert excluded == [{"id": "psch-04", "reason": "primary_address_mismatch"}]


def test_a_missing_primary_house_cannot_be_replaced_by_a_candidate_house() -> None:
    data = source()
    data["records"][0]["address_status"] = "house_missing"
    result, excluded = directory_facilities(data, coordinates(), PDF)
    assert result[0]["latitude"] is None
    assert excluded == [{"id": "psch-04", "reason": "primary_house_missing"}]


@pytest.mark.parametrize(
    "case",
    ["hash", "bytes", "duplicate", "orphan", "page", "readiness", "coordinate", "exit"],
)
def test_bad_sources_or_candidates_fail_before_export(case: str) -> None:
    data, points = source(), coordinates()
    if case == "hash":
        data["pdf_sha256"] = "0" * 64
    if case == "bytes":
        data["pdf_bytes"] += 1
    if case == "duplicate":
        data["records"].append(deepcopy(data["records"][0]))
    if case == "orphan":
        points["facilities"][0]["id"] = "psch-99"
    if case == "page":
        data["records"][0]["source_page"] = 13
    if case == "readiness":
        data["operational_status"] = "verified"
    if case == "coordinate":
        points["facilities"][0]["latitude"] = True
    if case == "exit":
        points["facilities"][0]["coordinate_status"] = "verified_fire_exit"
    with pytest.raises(ValueError):
        directory_facilities(data, points, PDF)


def test_reviewed_count_and_source_observation_are_required() -> None:
    data = source()
    data["address_rows_reviewed"] = 2
    with pytest.raises(ValueError, match="reviewed source count"):
        directory_facilities(data, coordinates(), PDF)
    data = source()
    data["observed_at"] = "2026-11-12T12:00:00"
    with pytest.raises(ValueError, match="timezone"):
        directory_facilities(data, coordinates(), PDF)
    data["observed_at"] = "2026-11-12"
    result, _ = directory_facilities(data, coordinates(), PDF)
    assert result[0]["observed_at"] == "2026-11-12"
