import pytest

from app.domain.road_references import lookup_keys, reference_key, shared_reference


@pytest.mark.parametrize("value", ["М-10", "М10", "M-10", "m 10", "м‑10"])
def test_reference_spellings_share_one_key(value: str) -> None:
    assert reference_key(value) == "м10"


def test_lookup_keys_cover_latin_and_cyrillic_forms() -> None:
    assert lookup_keys("M-10") == ["m10", "м10"]


def test_spelling_variants_and_joint_refs_resolve_to_one_road() -> None:
    assert shared_reference({"М-10", "М10", "М-10;А-107"}, "М-10") == ["М-10", "М10"]


def test_road_name_uses_reference_shared_by_all_candidates() -> None:
    assert shared_reference({"М-10", "М-10;А-107"}, "Россия") == ["М-10"]


def test_different_roads_stay_ambiguous() -> None:
    assert shared_reference({"Р-21", "А-181"}, "Кола") == []
