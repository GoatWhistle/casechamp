from normative_library_matching import library_address_matches


def test_matching_requires_postcode_locality_street_kind_and_house() -> None:
    source = "641751, Курганская обл., село Песчано-Коледино, ул. Ленина, д. 20А"
    tags = {
        "addr:postcode": "641751",
        "addr:city": "Песчано-Коледино",
        "addr:street": "улица Ленина",
        "addr:housenumber": "20А",
    }
    assert library_address_matches(source, tags)
    assert not library_address_matches(source, {**tags, "addr:postcode": "641752"})
    assert not library_address_matches(source, {**tags, "addr:city": "Ключевское"})
    assert not library_address_matches(source, {**tags, "addr:street": "переулок Ленина"})
    assert not library_address_matches(source, {**tags, "addr:housenumber": "20"})
    assert not library_address_matches(
        source, {k: v for k, v in tags.items() if k != "addr:postcode"}
    )


def test_expanded_rural_address_and_house_suffix_keep_exact_building() -> None:
    source = "641211, Юргамышский МО, с. Кипель, ул. Мира, 4 А"
    tags = {
        "addr:postcode": "641211",
        "addr:city": "Кипель",
        "addr:street": "улица Мира",
        "addr:housenumber": "4А",
    }
    assert library_address_matches(source, tags)
