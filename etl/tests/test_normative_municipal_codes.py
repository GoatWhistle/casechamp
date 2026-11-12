import pytest
from normative_municipal_codes import encoded_contexts


def reference() -> list[dict]:
    return [
        {"code": "37502000", "municipality_type": "municipal_okrug"},
        {"code": "37701000", "municipality_type": "urban_okrug"},
    ]


def test_exact_current_parent_encoding_does_not_recode_old_selsovet_identifiers() -> None:
    rows = encoded_contexts(["37502000101", "37606151111", "osm-way-123"], reference(), [])
    assert [r["point_id"] for r in rows] == ["37502000101"]
    assert rows[0]["municipality_code"] == "37502000"
    assert rows[0]["verification_status"] == "encoded_parent_2024_assignment_unconfirmed"
    assert rows[0]["structure_source_url"].startswith("https://www.nalog.gov.ru/")


def test_explicit_territorial_evidence_has_priority_over_encoded_reference() -> None:
    manual = {
        "point_id": "37502000101",
        "municipality_type": "urban_okrug",
        "source_url": "https://example.org/charter",
        "verification_status": "primary_verified",
    }
    assert encoded_contexts([manual["point_id"]], reference(), [manual]) == [manual]


def test_duplicate_reference_is_not_silently_resolved() -> None:
    with pytest.raises(ValueError, match="Duplicate municipality"):
        encoded_contexts(["37502000101"], reference() + reference(), [])
