import pytest

from app.domain.region_names import canonical_region

NAMES = [
    "Ненецкий автономный округ",
    "Ямало-Ненецкий автономный округ",
    "Ханты-Мансийский автономный округ — Югра",
    "Республика Северная Осетия — Алания",
    "Республика Саха (Якутия)",
    "Саратовская область",
    "Москва",
]


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("ЯНАО", "Ямало-Ненецкий автономный округ"),
        ("Ненецкий АО", "Ненецкий автономный округ"),
        ("ХМАО", "Ханты-Мансийский автономный округ — Югра"),
        ("Ханты-Мансийский автономный округ", "Ханты-Мансийский автономный округ — Югра"),
        ("Республика Северная Осетия", "Республика Северная Осетия — Алания"),
        ("Якутия", "Республика Саха (Якутия)"),
        ("саратовская  область", "Саратовская область"),
        ("Москва", "Москва"),
    ],
)
def test_atlas_and_colloquial_region_names_map_to_graph_names(value: str, expected: str) -> None:
    assert canonical_region(value, NAMES) == expected


@pytest.mark.parametrize("value", ["Ненецкий", "Нюрба", ""])
def test_ambiguous_or_unknown_names_stay_unresolved(value: str) -> None:
    assert canonical_region(value, NAMES) is None
