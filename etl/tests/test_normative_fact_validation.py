import json
from pathlib import Path

import import_normative
import pytest


@pytest.mark.parametrize("case", ["flags", "duplicate", "ids_shape", "territory"])
def test_invalid_fact_input_is_rejected_before_any_catalog_mutation(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, case: str
) -> None:
    datasets = tmp_path / "datasets"
    (datasets / "normative").mkdir(parents=True)
    (datasets / "normative/criteria.json").write_text("[]")
    (datasets / "normative-territories.json").write_text('{"territories":[]}')
    (datasets / "normative-settlements.json").write_text('{"settlements":[]}')
    fact = {
        "origin_id": "o",
        "service": "school",
        "source_url": "https://example.org/facts",
        "observed_at": "2026-11-12",
    }
    records = (
        [fact, fact]
        if case == "duplicate"
        else [
            {
                **fact,
                **(
                    {"facts_verified": "true"}
                    if case == "flags"
                    else {"eligible_facility_ids": "far"}
                ),
            }
        ]
    )
    if case == "territory":
        records = []
        (datasets / "normative-territories.json").write_text(
            json.dumps(
                {
                    "territories": [
                        {
                            "point_id": "37502000101",
                            "municipality_type": "municipal_okrug",
                            "source_url": "https://example.org/reference",
                            "structure_source_url": "https://example.org/rule",
                            "verification_status": "encoded_parent_2024_assignment_unconfirmed",
                            "municipality_code": "37504000",
                        }
                    ]
                }
            )
        )
    (datasets / "normative-walking-facts.json").write_text(json.dumps({"facts": records}))
    monkeypatch.setattr(import_normative, "ROOT", tmp_path)

    def forbidden_client() -> None:
        raise AssertionError("Storage must not be opened for invalid input")

    monkeypatch.setattr(import_normative, "ClickHouse", forbidden_client)
    error = TypeError if case == "ids_shape" else ValueError
    with pytest.raises(error, match="exact parent" if case == "territory" else None):
        import_normative.main()
