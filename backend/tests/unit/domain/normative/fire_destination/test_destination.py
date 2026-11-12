from collections.abc import Callable
from dataclasses import asdict
from typing import cast

import pytest

from app.domain.normative.fire_destination import FireDestination


def destination() -> FireDestination:
    return FireDestination(
        id="site-42",
        name="Object",
        address="Address",
        region="Region",
        latitude=55.10005,
        longitude=65.00005,
        source_url="https://example.org/objects",
        observed_at="2026-11-12",
        reference_status="verified_object",
        source_sha256="ab" * 32,
    )


@pytest.mark.parametrize(
    "changes",
    [
        {"id": ""},
        {"name": " "},
        {"address": None},
        {"region": ""},
        {"latitude": True},
        {"longitude": 181},
        {"latitude": float("nan")},
        {"observed_at": "2026-11-12T12:00:00"},
        {"source_url": "file:///tmp/source"},
        {"reference_status": "verified_exit"},
        {"source_sha256": "invalid"},
    ],
)
def test_malformed_destination_is_rejected(changes: dict[str, object]) -> None:
    constructor = cast(Callable[..., FireDestination], FireDestination)
    with pytest.raises((TypeError, ValueError)):
        constructor(**{**asdict(destination()), **changes})
