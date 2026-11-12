import json
from pathlib import Path

import import_normative
import pytest


@pytest.mark.parametrize("case", ["flags", "duplicate", "ids_shape", "validity", "population"])
def test_fire_evidence_is_validated_before_opening_storage(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: str,
) -> None:
    datasets = tmp_path / "datasets"
    (datasets / "normative").mkdir(parents=True)
    (datasets / "normative/criteria.json").write_text("[]")
    for filename, key in [
        ("normative-territories.json", "territories"),
        ("normative-settlements.json", "settlements"),
        ("normative-walking-facts.json", "facts"),
    ]:
        (datasets / filename).write_text(json.dumps({key: []}))
    fact = {
        "origin_id": "o", "source_url": "https://example.org/facts",
        "observed_at": "2026-11-12", "valid_from": "2026-11-01", "valid_until": "2026-11-30",
    }
    changes = {
        "flags": {"facts_verified": "false"},
        "ids_shape": {"eligible_facility_ids": "fire"},
        "validity": {"valid_until": "2026-10-31"},
        "population": {"population_verified": True},
    }
    records = [fact, fact] if case == "duplicate" else [{**fact, **changes[case]}]
    (datasets / "normative-library-facts.json").write_text('{"facts": []}')
    (datasets / "normative-medical-facts.json").write_text('{"facts": []}')
    (datasets / "normative-fire-facts.json").write_text(json.dumps({"facts": records}))
    monkeypatch.setattr(import_normative, "ROOT", tmp_path)

    def forbidden_client() -> None:
        raise AssertionError("Storage must not be opened for invalid fire evidence")

    monkeypatch.setattr(import_normative, "ClickHouse", forbidden_client)
    with pytest.raises(TypeError if case == "ids_shape" else ValueError):
        import_normative.main()
