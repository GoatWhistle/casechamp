import json
from typing import cast
from unittest.mock import Mock

import pytest

from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.records import decode, encode
from app.repository.clickhouse.traffic_state import ClickHouseTrafficStore
from app.usecase.traffic import TrafficAssignmentProgress, TrafficJob, TrafficScope


def test_saved_traffic_scope_before_new_search_loads_declared_defaults() -> None:
    job = TrafficJob("legacy", TrafficScope(region="R"), version="older")
    payload = encode(TrafficJob, job)
    for field in ["regions", "objective", "focus_bounds", "hypotheses"]:
        payload["scope"].pop(field)
    reader = Mock(spec=ClickHouseReader)
    reader.rows.return_value = [{"payload": json.dumps(payload)}]
    store = ClickHouseTrafficStore(cast(ClickHouseReader, reader))
    restored = store.load()[0]
    assert restored == job
    assert restored.scope.regions == []
    assert restored.scope.hypotheses == []
    assert restored.scope.objective == "connectivity"


def test_missing_required_record_field_is_not_silently_defaulted() -> None:
    payload = encode(TrafficJob, TrafficJob("required", TrafficScope()))
    payload.pop("id")
    with pytest.raises(KeyError, match="id"):
        decode(TrafficJob, payload)


def test_unversioned_history_is_not_reclassified_as_a_new_municipal_calculation() -> None:
    payload = encode(TrafficJob, TrafficJob('old', TrafficScope()))
    payload.pop('version')
    reader = Mock(spec=ClickHouseReader)
    reader.rows.return_value = [{'payload': json.dumps(payload)}]
    restored = ClickHouseTrafficStore(reader).load()[0]
    assert restored.version == 'legacy_unversioned'


def test_assignment_progress_survives_saved_job_reload() -> None:
    job = TrafficJob("municipal-progress", TrafficScope(),
                     assignment_progress=TrafficAssignmentProgress(7, .002))
    reader = Mock(spec=ClickHouseReader)
    reader.rows.return_value = [{"payload": json.dumps(encode(TrafficJob, job))}]
    assert ClickHouseTrafficStore(reader).load() == [job]


def test_saved_job_without_assignment_progress_remains_readable() -> None:
    job = TrafficJob("legacy", TrafficScope())
    payload = encode(TrafficJob, job)
    payload.pop("assignment_progress")
    assert decode(TrafficJob, payload) == job
