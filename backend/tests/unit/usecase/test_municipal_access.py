import json
from dataclasses import replace
from unittest.mock import Mock

import pytest

from app.domain.errors import DataUnavailable, InvalidQuery
from app.domain.normative.model import AccessRow
from app.usecase.municipal_access import MunicipalAccessQueries, MunicipalAccessSnapshot
from app.usecase.municipal_dataset import MunicipalSnapshotSource
from app.usecase.municipalities import MunicipalCollection, Municipality


def queries() -> tuple[MunicipalAccessQueries, Mock, Mock]:
    municipality = Municipality("district", "region", "District", 6,
        [[[(0., 0.), (2., 0.), (2., 2.), (0., 2.), (0., 0.)]]], "source", "today", "sha", "polygon", 1.)
    municipalities = Mock()
    municipalities.run.return_value = MunicipalCollection("region", [municipality], None)
    source = MunicipalSnapshotSource("region", "N01", "run", "scenario", "today", "graph",
        "model", "physical_only", "single_reference_point", json.dumps({"mode": "car", "unit": "minutes"}))
    rows = [AccessRow(str(i), f"Town {i}", 100, 1., 1., "facility", float(i), None, "unknown")
            for i in range(1, 11)]
    rows += [replace(rows[0], id="unreachable", minutes=None, state="unreachable"),
             replace(rows[0], id="unknown", minutes=None),
             replace(rows[0], id="outside", latitude=3., minutes=999.)]
    snapshot = Mock(return_value=MunicipalAccessSnapshot("digest", source, rows))
    facilities = Mock(return_value=[])
    return MunicipalAccessQueries(municipalities, snapshot, facilities), snapshot, facilities


def test_deficit_percentiles_exclude_unreachable_and_keep_unknown_separate() -> None:
    query, _, facilities = queries()
    result = query.run("region", "district", "N01", threshold=8., limit=2)
    assert result.reference_points == 12
    assert result.measured_points == 10
    assert result.unreachable_points == result.unresolved_points == 1
    assert result.p90 == 9.
    assert result.worst_decile_mean == 10.
    assert result.total == result.deficit_points == 3
    assert [p.row.id for p in result.points] == ["unreachable", "10"]
    facilities.assert_called_once_with("run", {"facility"})
    next_page = query.run("region", "district", "N01", 8., offset=2, limit=2)
    assert [p.row.id for p in next_page.points] == ["9"]
    assert next_page.p90 == result.p90


def test_walking_uses_distance_and_keeps_threshold_equality_within() -> None:
    query, snapshot, _ = queries()
    old = snapshot.return_value
    snapshot.return_value = replace(old, source=replace(old.source, criterion_id="N04",
        metadata_json=json.dumps({"mode": "walk", "unit": "metres"})),
        rows=[replace(old.rows[0], distance_metres=500.)])
    result = query.run("region", "district", "N04", 500.)
    assert result.unit == "metres"
    assert result.p90 == 500.
    assert result.total == 0


@pytest.mark.parametrize("threshold", [0., -1., float("inf"), float("nan")])
def test_invalid_threshold_is_rejected_before_reading_snapshot(threshold: float) -> None:
    query, snapshot, _ = queries()
    with pytest.raises(InvalidQuery):
        query.run("region", "district", "N01", threshold)
    snapshot.assert_not_called()


def test_missing_publication_is_not_an_empty_success() -> None:
    query, snapshot, _ = queries()
    snapshot.return_value = None
    with pytest.raises(DataUnavailable):
        query.run("region", "district", "N01")


def test_wrong_municipality_is_rejected() -> None:
    query, snapshot, _ = queries()
    with pytest.raises(InvalidQuery):
        query.run("region", "other", "N01")
    snapshot.assert_not_called()


def test_selected_points_cache_changes_with_snapshot_digest() -> None:
    query, snapshot, _ = queries()
    first = query.run("region", "district", "N01")
    snapshot.return_value = replace(snapshot.return_value, sha256="new-digest", rows=[])
    second = query.run("region", "district", "N01")
    assert first.reference_points == 12
    assert second.reference_points == 0
    assert second.p90 is None
