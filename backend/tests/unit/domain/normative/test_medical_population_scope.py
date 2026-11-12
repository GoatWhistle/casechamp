import pytest

from app.domain.normative.model import AccessRow, Criterion, coverage
from app.domain.normative.scope import apply_population_scope


@pytest.mark.parametrize("service", ["emergency_cardiology", "urgent_cardiology"])
def test_attached_adult_cardiology_does_not_inherit_all_resident_population(service: str) -> None:
    criterion = Criterion(
        "N01",
        service,
        "132n",
        "2",
        "https://example.org",
        "2016-02-27",
        60,
        "minutes",
        "car",
        "Region",
        "placement_requirement",
        "unconfirmed",
    )
    original = [AccessRow("a", "A", 100, 55, 65, "hospital", 20, 0, "within")]
    rows = apply_population_scope(criterion, original)
    assert rows[0].minutes == 20
    assert rows[0].facility_id == "hospital"
    assert rows[0].population is None
    assert rows[0].state == "unknown"
    assert "medical_catchment_unconfirmed" in rows[0].uncertainty
    assert coverage(rows).lower_percent is None
    assert original[0].population == 100 and original[0].state == "within"


def test_general_population_service_preserves_its_geographic_model_coverage() -> None:
    criterion = Criterion(
        "N05",
        "mfc",
        "178",
        "5",
        "https://example.org",
        "2023-02-08",
        60,
        "minutes",
        "car",
        "Region",
        "placement_requirement",
        "unconfirmed",
    )
    rows = [AccessRow("a", "A", 100, 55, 65, "mfc", 20, 0, "within")]
    assert apply_population_scope(criterion, rows) is rows
    assert coverage(rows).lower_percent == 100
