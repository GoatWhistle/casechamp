from types import SimpleNamespace
from typing import cast

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.controller.municipalities.router import build_municipality_router
from app.domain.errors import DataUnavailable, RegionNotFound
from app.usecase.interface import AtlasRepository
from app.usecase.municipalities import Municipality, MunicipalityQueries


class MunicipalSource:
    def __init__(self, available: bool = True, empty: bool = False) -> None:
        self.available = available
        self.empty = empty

    def boundaries(self, region_id: str) -> list[Municipality]:
        if not self.available:
            raise DataUnavailable()
        if self.empty:
            return []
        return [
            Municipality(
                "osm-relation-1",
                region_id,
                "Real source name",
                6,
                [[[(40.0, 44.0), (41.0, 44.0), (41.0, 45.0), (40.0, 44.0)]]],
                "https://www.openstreetmap.org/relation/1",
                "2026-11-11",
                "abc",
                "max_polygon_overlap",
                0.99,
            )
        ]


def queries(source: MunicipalSource) -> MunicipalityQueries:
    atlas = cast(AtlasRepository, SimpleNamespace(regions=lambda: [SimpleNamespace(id="07000000")]))
    return MunicipalityQueries(source, atlas)


def test_real_geometry_and_provenance_are_preserved_in_http_response() -> None:
    app = FastAPI()
    app.include_router(build_municipality_router(queries(MunicipalSource())))
    data = TestClient(app).get("/regions/07000000/municipalities").json()
    assert data["type"] == "FeatureCollection"
    assert data["metadata"]["reason"] == "partial_source_coverage"
    assert data["metadata"]["coverage_status"] == "available"
    feature = data["features"][0]
    assert feature["geometry"]["type"] == "MultiPolygon"
    assert feature["properties"]["source_sha256"] == "abc"
    assert feature["properties"]["admin_level"] == 6


@pytest.mark.parametrize(
    "source,reason",
    [
        (MunicipalSource(available=False), "municipal_storage_unavailable"),
        (MunicipalSource(empty=True), "municipal_geometry_not_imported"),
    ],
)
def test_unavailable_does_not_invent_districts(source: MunicipalSource, reason: str) -> None:
    result = queries(source).run("07000000")
    assert not result.items
    assert result.reason == reason


def test_unknown_region_is_not_an_empty_success() -> None:
    with pytest.raises(RegionNotFound):
        queries(MunicipalSource()).run("unknown")
