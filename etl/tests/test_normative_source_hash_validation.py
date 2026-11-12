import json
from pathlib import Path

import import_normative
import pytest


def test_invalid_facility_source_hash_fails_before_opening_storage(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    folder = tmp_path / "datasets/normative"
    folder.mkdir(parents=True)
    (folder / "criteria.json").write_text("[]")
    (folder / "fire.json").write_text(
        json.dumps(
            {
                "facilities": [
                    {
                        "id": "depot",
                        "service": "fire",
                        "name": "Depot",
                        "address": "Address",
                        "source_url": "https://example.org/source",
                        "observed_at": "2026-11-12",
                        "latitude": None,
                        "longitude": None,
                        "coordinate_source": None,
                        "coordinate_status": "missing",
                        "source_sha256": "invalid",
                    }
                ]
            }
        )
    )
    monkeypatch.setattr(import_normative, "ROOT", tmp_path)

    def forbidden_client() -> None:
        raise AssertionError("Invalid source hashes must not open storage")

    monkeypatch.setattr(import_normative, "ClickHouse", forbidden_client)
    with pytest.raises(ValueError, match="SHA256"):
        import_normative.main()
