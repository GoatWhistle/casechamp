import json
from dataclasses import asdict, replace
from hashlib import sha256
from pathlib import Path
from types import SimpleNamespace
from typing import cast
from unittest.mock import Mock, patch

from app.domain.normative.model import AccessRow, Facility
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.municipal_published import ClickHouseMunicipalPublished
from app.repository.files.municipal_dataset import JsonMunicipalDataset
from app.usecase.municipal_dataset import MunicipalSnapshotSource, persist_aggregation
from app.usecase.municipalities import Municipality
from app.usecase.normative.regional_catalog import RegionalCatalogQueries
from app.usecase.normative.regional_models import REGIONAL_ROAD_REVISION


class Reader:
    graph = "graph"

    def rows(self, sql: str, parameters: dict[str, str]) -> list[dict[str, str]]:
        if "regional_measurements" in sql:
            return [{"criterion_id": "N04", "run_id": "real-run"}]
        if "pedestrian_networks" in sql:
            return [{"revision": self.graph}]
        return [{"key": "graph_revision", "value": self.graph}]


def test_published_values_require_exact_run_graph_catalog_and_geometry(tmp_path: Path) -> None:
    facility = Facility(
        "f",
        "school",
        "Source",
        "",
        "https://source",
        "2026-11-11",
        44,
        40,
        "osm",
        "osm_institution_pin",
    )
    facilities = [facility]
    fingerprint = sha256(
        json.dumps([asdict(facility)], sort_keys=True, allow_nan=False).encode()
    ).hexdigest()
    source = MunicipalSnapshotSource(
        "07000000",
        "N04",
        "real-run",
        "scenario",
        "2026-11-13",
        "graph",
        "walk-model",
        "physical_only",
        "single_reference_point",
        json.dumps({"unit": "metres", "mode": "walk", "catalog_fingerprint": fingerprint}),
    )
    dataset = JsonMunicipalDataset(tmp_path)
    digest = dataset.snapshot(
        source,
        [
            AccessRow(
                "home", "Home", None, 44.2, 40.2, "f", None, None, "unknown", distance_metres=300
            )
        ],
    )
    municipality = Municipality(
        "osm-relation-1",
        "07000000",
        "Real",
        6,
        [[[(40, 44), (41, 44), (41, 45), (40, 45), (40, 44)]]],
        "https://boundary",
        "2026-11-11",
        "abc",
        "polygon",
        1,
    )
    dataset.boundaries([municipality])
    persist_aggregation(dataset, digest, municipality)
    reader = Reader()
    catalog = cast(
        RegionalCatalogQueries,
        SimpleNamespace(catalog=lambda *args: SimpleNamespace(facilities=facilities)),
    )
    published = ClickHouseMunicipalPublished(
        cast(ClickHouseReader, reader), dataset, catalog, boundaries=lambda region: [municipality]
    )
    assert published.values(municipality)[0].value == 100
    with patch.object(dataset, "source", wraps=dataset.source) as read_source:
        batch = published.overview([municipality, replace(municipality, id="missing")], "N04")
        assert batch[municipality.id][0].value == 100
        assert batch["missing"] == []
        read_source.assert_called_once()
    with patch.object(dataset, "rows", wraps=dataset.rows) as read:
        first = published.snapshot(municipality, "N04")
        assert first is not None
        assert published.snapshot(municipality, "N04") is first
        read.assert_called_once()

    assert published.values(replace(municipality, source_sha256="different")) == []
    reader.graph = "changed-graph"
    assert published.values(municipality) == []
    assert published.snapshot(municipality, "N04") is None
    reader.graph = "graph"
    facilities.append(replace(facility, id="new-facility"))
    published._cache.clear()
    assert published.values(municipality) == []


def test_cross_border_measurement_validates_against_cross_border_catalog(tmp_path: Path) -> None:
    reader = Mock()
    reader.rows.return_value = [{"criterion_id": "N01", "run_id": "cross-border",
                                 "model_revision": REGIONAL_ROAD_REVISION}]
    catalog = Mock()
    catalog.catalog.return_value.facilities = []
    published = ClickHouseMunicipalPublished(reader, JsonMunicipalDataset(tmp_path), catalog,
                                            boundaries=lambda region: [])
    published._versions("region")
    catalog.catalog.assert_called_once_with("region", "N01", cross_region=True)
    assert "JSONExtractString(payload,'model_revision')" in reader.rows.call_args.args[0]


def test_selected_service_does_not_load_unrelated_national_catalogs() -> None:
    reader = Mock()
    reader.rows.return_value = [
        {'criterion_id': 'N01', 'run_id': 'medical', 'model_revision': REGIONAL_ROAD_REVISION},
        {'criterion_id': 'N04', 'run_id': 'school', 'model_revision': 'walk'},
    ]
    catalog = Mock()
    catalog.catalog.return_value.facilities = []
    published = ClickHouseMunicipalPublished(reader, Mock(), catalog, boundaries=lambda region: [])
    assert set(published._versions('region', 'N04')) == {'N04'}
    catalog.catalog.assert_called_once_with('region', 'N04')
    assert set(published._versions('region', 'N04')) == {'N04'}
    catalog.catalog.assert_called_once()
    assert set(published._versions('region', 'N01')) == {'N01'}
    catalog.catalog.assert_called_with('region', 'N01', cross_region=True)
    assert set(published._versions('region')) == {'N01', 'N04'}
