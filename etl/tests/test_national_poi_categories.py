from national_poi_categories import categories


def test_generic_healthcare_does_not_become_verified_adult_cardiology() -> None:
    assert categories({"amenity": "hospital"}) == ["medical"]
    assert categories({"amenity": "clinic", "healthcare": "clinic"}) == ["medical"]


def test_private_employment_offices_remain_candidates_not_public_service_proof() -> None:
    assert categories({"office": "employment_agency", "name": "Private agency"}) == ["employment_candidate"]


def test_mfc_candidate_requires_specific_office_or_government_name() -> None:
    assert categories({"office": "government", "name": "МФЦ Мои документы"}) == ["mfc_candidate"]
    assert categories({"office": "government", "name": "Administration"}) == []


def test_platform_without_bus_tag_is_not_silently_a_bus_stop() -> None:
    assert categories({"public_transport": "platform", "train": "yes"}) == []
    assert categories({"public_transport": "platform", "bus": "yes"}) == ["stop"]
    assert categories({"highway": "bus_stop"}) == ["stop"]
