from collections.abc import Callable
from dataclasses import asdict, replace
from datetime import UTC, datetime, timedelta
from typing import cast

import pytest
from tests.unit.domain.normative.library.factories import INSTANT, facts

from app.domain.normative.library.facts import LibraryFacts


@pytest.mark.parametrize(
    "changes",
    [
        {"facts_verified": "false"},
        {"facts_verified": 1},
        {"facts_verified": None},
        {"population": True},
        {"population": -1},
        {"population": 1.2},
        {"population_reference": None},
        {"municipality_code": "37502000101"},
        {"municipality_type": "village"},
        {"valid_from": "2026-12-01"},
        {"observed_at": "2026-11-10T12:00:00"},
        {"source_url": "file:///tmp/evidence"},
        {"origin_latitude": float("nan")},
        {"origin_longitude": 181},
        {"approach_metres": True},
        {"approach_metres": 5001},
        {"routing_node": True},
        {"measurement_graph_revision": None},
        {"legal_edition_date": None},
        {"eligible_facility_ids": ["library"]},
        {"eligible_facility_ids": ("library", "library")},
        {"verified_closed_way_ids": (True,)},
        {"verified_closed_way_ids": (12, 12)},
        {"transport_mode": "bus"},
    ],
)
def test_malformed_attestations_are_rejected_without_coercion(changes: dict[str, object]) -> None:
    with pytest.raises((ValueError, TypeError)):
        cast(Callable[..., LibraryFacts], LibraryFacts)(**{**asdict(facts()), **changes})


def test_validity_uses_utc_and_observation_time_without_guessing_naive_timezones() -> None:
    evidence = replace(facts(), observed_at="2026-11-12T12:00:00+00:00")
    assert evidence.active_on(INSTANT)
    assert not evidence.active_on(INSTANT - timedelta(microseconds=1))
    assert evidence.active_on(datetime(2026, 11, 12, 14, tzinfo=UTC).astimezone())
    assert not evidence.active_on(datetime(2026, 12, 1, tzinfo=UTC))
    with pytest.raises(ValueError, match="timezone"):
        evidence.active_on(INSTANT.replace(tzinfo=None))
