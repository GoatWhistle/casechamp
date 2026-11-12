from dataclasses import asdict

import pytest
from tests.unit.domain.normative.fire_evidence.factories import facility

from app.domain.normative.model import Facility


@pytest.mark.parametrize(
    "changes",
    [
        {"coordinate_snapshot_sha256": "ab" * 32},
        {"coordinate_snapshot_url": "https://example.org/extract"},
        {"coordinate_snapshot_sha256": "bad", "coordinate_snapshot_url": "https://example.org"},
        {"coordinate_snapshot_sha256": "ab" * 32, "coordinate_snapshot_url": "file:///local"},
        {
            "coordinate_snapshot_sha256": "ab" * 32,
            "coordinate_snapshot_url": "https://example.org",
            "latitude": None,
        },
        {
            "coordinate_snapshot_sha256": "ab" * 32,
            "coordinate_snapshot_url": "https://example.org",
            "coordinate_source": None,
        },
    ],
)
def test_incomplete_or_unbound_coordinate_snapshots_are_rejected(changes: dict[str, object]) -> None:
    values = asdict(facility())
    values.update(changes)
    with pytest.raises(ValueError):
        Facility(**values)
