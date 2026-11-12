from normative_library_deduplication import deduplicate


def test_same_author_and_address_reuses_existing_point_but_keeps_distinct_profiles() -> None:
    existing = [
        {
            "id": "city-1",
            "service": "library",
            "name": "Библиотека им. М. Горького",
            "address": "640040, Курган, Алексеева, 4",
        }
    ]
    source = [
        {
            "id": "card-1",
            "service": "library",
            "name": "Библиотека №1 им. М. Горького МБУК БИС",
            "address": "г. Курган, ул. Алексеева, д. 4",
            "published_on": "2023-01-01",
            "source_url": "https://example.org/1",
        },
        {
            "id": "card-2",
            "service": "children_library",
            "name": "Библиотека им. М. Горького",
            "address": "г. Курган, ул. Алексеева, д. 4",
            "published_on": "2024-01-01",
            "source_url": "https://example.org/2",
        },
        {
            "id": "card-3",
            "service": "library",
            "name": "Библиотека им. А. Пушкина",
            "address": "г. Курган, ул. Алексеева, д. 4",
            "published_on": "2024-01-01",
            "source_url": "https://example.org/3",
        },
    ]
    retained, aliases = deduplicate(source, existing)
    assert [r["id"] for r in retained] == ["card-2", "card-3"]
    assert aliases == [
        {
            "source_url": "https://example.org/1",
            "retained_id": "city-1",
            "reason": "same_profile_name_address",
        }
    ]


def test_newest_matching_card_retains_history_alias_and_different_house_is_separate() -> None:
    rows = [
        {
            "id": key,
            "service": "library",
            "name": "Сельская библиотека",
            "address": address,
            "published_on": date,
            "source_url": "https://example.org/" + key,
        }
        for key, address, date in [
            ("old", "с. Кетово, ул. Мира, 1", "2020-01-01"),
            ("new", "с. Кетово, ул. Мира, 1", "2026-01-01"),
            ("other", "с. Кетово, ул. Мира, 2", "2026-01-01"),
        ]
    ]
    retained, aliases = deduplicate(rows, [])
    assert [r["id"] for r in retained] == ["new", "other"]
    assert aliases[0]["retained_id"] == "new"
