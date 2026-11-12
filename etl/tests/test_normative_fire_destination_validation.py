import json
from pathlib import Path

import import_normative
import pytest


@pytest.mark.parametrize("case", ["duplicate", "coordinate", "source", "status", "hash"])
def test_invalid_fire_destination_never_opens_storage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: str,
) -> None:
    datasets = tmp_path / "datasets"
    (datasets / "normative").mkdir(parents=True)
    (datasets / "normative/criteria.json").write_text("[]")
    for filename, key in [
        ("normative-territories.json", "territories"),
        ("normative-settlements.json", "settlements"),
        ("normative-walking-facts.json", "facts"),
        ("normative-library-facts.json", "facts"),
        ("normative-medical-facts.json", "facts"),
        ("normative-fire-facts.json", "facts"),
    ]:
        (datasets / filename).write_text(json.dumps({key: []}))
    record = {
        "id": "object-42", "name": "Destination", "address": "Address", "region": "Region",
        "latitude": 55, "longitude": 65, "source_url": "https://example.org/objects",
        "observed_at": "2026-11-12",
    }
    changes = {
        "coordinate": {"latitude": True}, "source": {"source_url": "file:///local"},
        "status": {"reference_status": "verified_entrance"}, "hash": {"source_sha256": "bad"},
    }
    records = [record, record] if case == "duplicate" else [{**record, **changes[case]}]
    (datasets / "normative-fire-destinations.json").write_text(json.dumps({"destinations": records}))
    monkeypatch.setattr(import_normative, "ROOT", tmp_path)

    def forbidden_client() -> None:
        raise AssertionError("Invalid destinations must not open or truncate storage")

    monkeypatch.setattr(import_normative, "ClickHouse", forbidden_client)
    with pytest.raises((TypeError, ValueError)):
        import_normative.main()
