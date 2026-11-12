from normative_address import address_matches


def test_house_in_another_city_is_rejected() -> None:
    row = {"city": "Шадринск", "road": "улица Пушкина", "house_number": "58"}
    assert not address_matches("г. Курган, ул. Пушкина, 58", row)


def test_street_and_lane_are_not_interchangeable() -> None:
    row = {"village": "Введенское", "road": "переулок Пушкина", "house_number": "11"}
    assert not address_matches("с. Введенское, ул. Пушкина, стр. 11", row)


def test_full_address_matches_without_confusing_municipality_and_city() -> None:
    row = {"city": "Курган", "road": "улица Куйбышева", "house_number": "144"}
    assert address_matches("г.о. город Курган, г.Курган, ул. Куйбышева, стр. 144", row)


def test_different_house_and_missing_address_are_rejected() -> None:
    row = {"village": "Кетово", "road": "улица Космонавтов", "house_number": "46"}
    assert not address_matches("с. Кетово, ул. Космонавтов, д. 45, помещ. 3", row)
    assert not address_matches("Курган", {})
