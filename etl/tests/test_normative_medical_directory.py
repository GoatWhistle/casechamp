import hashlib
import json
from pathlib import Path

import pytest
from normative_medical_directory import care_forms, directory_facilities

ROOT = Path(__file__).resolve().parents[2]


def reviewed() -> tuple[dict, dict, bytes]:
    source = json.loads((ROOT / "datasets/normative-medical-source-records.json").read_text())
    candidates = json.loads((ROOT / "datasets/normative-medical-coordinate-candidates.json").read_text())
    pdf = b"isolated reviewed source byte fixture"
    source.update(pdf_sha256=hashlib.sha256(pdf).hexdigest(), pdf_bytes=len(pdf))
    return source, candidates, pdf


def test_complete_reviewed_table_expands_forms_without_guessing_coordinates_or_population() -> None:
    source, candidates, pdf = reviewed()
    result, excluded = directory_facilities(source, candidates, pdf)
    assert len(result) == 32
    assert len({(row["id"], row["service"]) for row in result}) == 32
    assert {row["service"] for row in result} == {"emergency_cardiology", "urgent_cardiology"}
    assert excluded == [{"id": "shadrinsk-district-hospital", "source_page": 11,
                         "reason": "planned_cardiology_only"}]
    assert sum(row["latitude"] is not None for row in result) == 4
    for row in result:
        assert "population" not in row and row["published_on"] is None
        assert row["source_sha256"] == source["pdf_sha256"]
        assert row["observed_at"] == "2026-11-12"
        assert "#page=" in row["source_url"]
    zero_beds = next(r for r in source["records"] if r["id"] == "interdistrict-hospital-1")
    assert zero_beds["cardiology_beds"] == 0
    assert len([r for r in result if r["id"] == zero_beds["id"]]) == 2
    for original in candidates["facilities"]:
        for row in (r for r in result if r["id"] == original["id"]):
            for field in ("latitude", "longitude", "coordinate_source", "coordinate_status"):
                assert row[field] == original[field]


@pytest.mark.parametrize("value", ["Экстренная неврология", "Кардиология", "Экстренная, экстренная кардиология"])
def test_other_profiles_and_ambiguous_forms_are_not_transferred(value: str) -> None:
    with pytest.raises(ValueError):
        care_forms(value)


@pytest.mark.parametrize("case", ["bytes", "identity", "count", "duplicate", "page", "status", "address"])
def test_conflicting_medical_source_or_geometry_is_rejected(case: str) -> None:
    source, candidates, pdf = reviewed()
    if case == "bytes":
        pdf += b"changed"
    elif case == "identity":
        source["act"] = "1169"
    elif case == "count":
        source["address_rows_reviewed"] += 1
    elif case == "duplicate":
        source["records"][-1]["id"] = source["records"][0]["id"]
    elif case == "page":
        source["records"][0]["source_page"] = 135
    elif case == "status":
        candidates["facilities"][0]["coordinate_status"] = "verified_medical_entrance"
    else:
        candidates["facilities"][0]["address"] = "Another address"
    with pytest.raises(ValueError):
        directory_facilities(source, candidates, pdf)
