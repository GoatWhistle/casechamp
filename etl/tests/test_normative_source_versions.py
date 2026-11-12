from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path

import pytest
from stamp_normative_sources import build, verified_document


def example() -> tuple[bytes, dict, list[dict]]:
    raw = b'original source response'
    original = {
        "id": "site-1", "service": "mfc", "name": "Office", "address": "Address",
        "source_url": "https://example.org/directory",
    }
    document = {
        "sha256": sha256(raw).hexdigest(), "bytes": len(raw),
        "observed_at": "2026-11-12",
        "facilities": [{**original, "observed_at": "2026-11-12", "latitude": 55,
                        "longitude": 65, "coordinate_source": "https://example.org/geometry"}],
    }
    return raw, document, [original]


def test_stamp_keeps_geometry_observation_and_source_document_distinct() -> None:
    raw, document, records = example()
    before = deepcopy(document)
    stamped = verified_document(raw, document, records)
    assert document == before
    assert stamped["facilities"][0] == {
        **document["facilities"][0], "source_sha256": sha256(raw).hexdigest(),
    }
    assert verified_document(raw, stamped, records) == stamped


@pytest.mark.parametrize("case", ["hash", "bytes", "inventory", "address", "observation", "geometry", "conflict", "duplicate"])
def test_stamp_rejects_weak_or_conflicting_source_chain(case: str) -> None:
    raw, document, records = example()
    if case == "hash":
        raw += b"changed"
    elif case == "bytes":
        document["bytes"] += 1
    elif case == "inventory":
        records[0]["id"] = "another-id"
    elif case == "address":
        records[0]["address"] = "Another address"
    elif case == "observation":
        document["facilities"][0]["observed_at"] = "2026-10-01"
    elif case == "geometry":
        records[0]["latitude"] = 56
    elif case == "conflict":
        document["facilities"][0]["source_sha256"] = "0" * 64
    else:
        records.append(dict(records[0]))
    before = deepcopy(document)
    with pytest.raises(ValueError):
        verified_document(raw, document, records)
    assert document == before


def test_acquisition_manifest_must_bind_url_and_observation(tmp_path: Path) -> None:
    raw, document, _ = example()
    source = {"id": "schools", "url": "https://example.org/actual", "sha256": document["sha256"],
              "bytes": len(raw), "received_at": document["observed_at"]}
    document.update({**source, "url": "https://example.org/substituted"})
    folder = tmp_path / "datasets/normative"
    folder.mkdir(parents=True)
    (folder / "schools.json").write_text(json.dumps(document))
    inputs = tmp_path / ".local/normative-inputs"
    inputs.mkdir(parents=True)
    (inputs / "manifest.json").write_text(json.dumps([source]))
    with pytest.raises(ValueError, match="acquisition manifest"):
        build(tmp_path, "schools")
