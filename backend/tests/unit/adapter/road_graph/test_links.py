import pytest

from app.adapter.road_graph.links import (
    apply_manual,
    apply_trunk,
    canonical_links,
    intercity_links,
    local_links,
    missing_removals,
)
from app.domain.errors import InvalidQuery
from app.usecase.transport_links import LinkChange, validate_links

TRUNK = [
    ("Москва", "Тверь", "rail", 2.0),
    ("Тверь", "Москва", "rail", 2.0),
    ("Москва", "Сургут", "air", 3.5),
    ("Сургут", "Москва", "air", 3.5),
    ("Сургут", "Тюмень", "air", 1.2),
    ("Тюмень", "Сургут", "air", 1.2),
    ("Москва", "Сургут", "rail", 40.0),
]
MANUAL = [("1", "2", 30.0, "ferry"), ("2", "3", 25.0, "air")]


def test_airport_closure_removes_every_air_link_of_city_only() -> None:
    kept = apply_trunk(TRUNK, [LinkChange("remove", "intercity", "air", "Сургут", "*")])
    assert ("Москва", "Сургут", "rail", 40.0) in kept
    assert not [row for row in kept if row[2] == "air" and "Сургут" in row[:2]]
    assert len(kept) == 3


def test_added_intercity_link_is_bidirectional() -> None:
    kept = apply_trunk(TRUNK, [LinkChange("add", "intercity", "rail", "Москва", "Тверь", 1.0)])
    assert ("Москва", "Тверь", "rail", 1.0) in kept and ("Тверь", "Москва", "rail", 1.0) in kept


def test_local_removal_matches_both_directions_and_mode() -> None:
    kept = apply_manual(MANUAL, [LinkChange("remove", "local", "ferry", "2", "1")])
    assert kept == [("2", "3", 25.0, "air")]
    added = apply_manual(MANUAL, [LinkChange("add", "local", "river", "1", "3", 5.0)])
    assert ("1", "3", 5.0, "river") in added


def test_absent_removal_is_reported() -> None:
    links = [
        LinkChange("remove", "intercity", "air", "Москва", "Тверь"),
        LinkChange("remove", "local", "ferry", "1", "2"),
    ]
    assert missing_removals(TRUNK, MANUAL, links) == links[:1]


def test_intercity_names_are_canonical_market_cities() -> None:
    links = canonical_links(
        [LinkChange("add", "intercity", "rail", "г. Москва", "тверь", 1.0)], ["Москва", "Тверь"]
    )
    assert (links[0].source, links[0].target) == ("Москва", "Тверь")
    with pytest.raises(InvalidQuery):
        canonical_links([LinkChange("remove", "intercity", "air", "Деревня", "*")], ["Москва"])


def test_listing_deduplicates_directions_and_filters_mode() -> None:
    links = intercity_links(TRUNK, "Сургут", "air")
    assert [(l.source, l.target, l.hours) for l in links] == [
        ("Сургут", "Тюмень", 1.2),
        ("Москва", "Сургут", 3.5),
    ]
    rows = [("1", "село Хоро", "2", "г. Нюрба", "ferry", 30.0, "Якутия")]
    assert local_links(rows, "Нюрба", None)[0].target_name == "г. Нюрба"
    assert local_links(rows, "Якутия", "air") == []


@pytest.mark.parametrize(
    "link",
    [
        LinkChange("add", "intercity", "rail", "Москва", "Тверь"),
        LinkChange("add", "intercity", "rail", "Москва", "*", 1.0),
        LinkChange("remove", "intercity", "ferry", "Москва", "Тверь"),
        LinkChange("close", "local", "air", "1", "2"),
        LinkChange("add", "local", "air", "1", "1", 2.0),
        LinkChange("add", "local", "air", "1", "2", 80.0),
    ],
)
def test_invalid_links_are_rejected(link: LinkChange) -> None:
    with pytest.raises(InvalidQuery):
        validate_links([link])
