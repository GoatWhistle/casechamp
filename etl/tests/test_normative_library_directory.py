from copy import deepcopy

import pytest
from normative_library_directory import directory_facilities


def source() -> dict:
    return {
        "reviewed_on": "2026-11-12",
        "snapshot_kind": "reviewed_web_reader_fields",
        "records": [
            {
                "source_url": "https://yugovalib.ru/site/view/334",
                "name": "Центральная библиотека",
                "address": "с. Кетово, ул. Космонавтов, 43",
                "published_on": "2025-07-02",
            },
            {
                "source_url": "https://yugovalib.ru/site/view/5720",
                "name": "Детская библиотека",
                "address": "с. Кетово, ул. Космонавтов, 43",
                "published_on": "2023-07-20",
            },
            {
                "source_url": "https://yugovalib.ru/site/view/292",
                "name": "Библиотека КГСХА",
                "address": None,
                "published_on": "2019-08-06",
            },
        ],
    }


def test_distinct_library_profiles_preserve_shared_address_without_inventing_coordinates() -> None:
    original = source()
    before = deepcopy(original)
    facilities, excluded = directory_facilities(original, "2026-11-12T05:00:00+00:00")
    assert original == before
    assert len(facilities) == 2
    assert [row["service"] for row in facilities] == ["library", "children_library"]
    assert facilities[0]["address"] == facilities[1]["address"]
    assert all(
        row["latitude"] is None and row["coordinate_status"] == "missing" for row in facilities
    )
    assert all(row["observed_at"] != "2025-07-02" for row in facilities)
    assert excluded == [
        {"source_url": "https://yugovalib.ru/site/view/292", "reason": "missing_address"}
    ]


@pytest.mark.parametrize("change", ["duplicate", "foreign_source", "invalid_date", "unreviewed"])
def test_invalid_directory_fails_before_output(change: str) -> None:
    record = source()
    if change == "duplicate":
        record["records"].append(record["records"][0])
    elif change == "foreign_source":
        record["records"][0]["source_url"] = "https://example.org/site/view/334"
    elif change == "invalid_date":
        record["records"][0]["published_on"] = "yesterday"
    else:
        record["snapshot_kind"] = "unreviewed"
    with pytest.raises(ValueError):
        directory_facilities(record, "2026-11-12T05:00:00+00:00")


def test_closed_and_ambiguous_sources_do_not_become_targets() -> None:
    record = source()
    record["records"][0]["operational_status"] = "explicitly_closed"
    record["records"][1]["read_status"] = "ambiguous"
    facilities, excluded = directory_facilities(record, "2026-11-12")
    assert facilities == []
    assert [row["reason"] for row in excluded] == [
        "explicitly_closed",
        "ambiguous",
        "missing_address",
    ]


def test_reviewed_body_can_establish_profile_without_a_matching_title_word() -> None:
    record = source()
    record["records"] = [record["records"][0]]
    record["records"][0]["name"] = "Карандашовское структурное подразделение"
    record["records"][0]["profile_hint"] = "library"
    facilities, _ = directory_facilities(record, "2026-11-12")
    assert facilities[0]["service"] == "library"
    assert facilities[0]["published_on"] == "2025-07-02"
