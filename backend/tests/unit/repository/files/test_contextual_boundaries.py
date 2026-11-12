import json
from pathlib import Path
from types import SimpleNamespace
from typing import cast

import pytest
from shapely.geometry import MultiPolygon, Point, Polygon

from app.adapter.atlas.outside_mask import AtlasOutsideMask
from app.domain.errors import DataUnavailable
from app.repository.files.contextual_boundaries import JsonContextualBoundaryRepository
from app.usecase.dto import BoundaryShape
from app.usecase.interface import AtlasRepository
from app.usecase.reference import ReferenceQueries


def source(path: Path, display_only: bool = True) -> None:
    path.write_text(
        json.dumps(
            {
                "contextual_regions": [
                    {
                        "id": "context-source",
                        "name": "Source territory",
                        "bounds": [30, 45, 31, 46],
                        "polygons": [[[[30, 45], [31, 45], [31, 46], [30, 46], [30, 45]]]],
                        "source_url": "https://example.org/source",
                        "observed_at": "2017",
                        "source_sha256": "abc",
                        "source_name": "Source ADM1",
                        "source_iso": "UA-00",
                        "source_shape_id": "source-id",
                        "geometry_basis": "source_adm1",
                        "disputed_status": "disputed_control_and_sovereignty",
                        "display_only": display_only,
                        "analytics_enabled": False,
                    }
                ]
            }
        )
    )


def test_contextual_boundaries_remain_separate_and_only_affect_display_mask(tmp_path: Path) -> None:
    path = tmp_path / "context.json"
    source(path)
    region = BoundaryShape(
        "07000000",
        "Analytical",
        (40, 44, 41, 45),
        [[[(40, 44), (41, 44), (41, 45), (40, 45), (40, 44)]]],
    )
    atlas = cast(
        AtlasRepository,
        SimpleNamespace(
            regions=lambda: [SimpleNamespace(id="07000000", name="Analytical")],
            boundaries=lambda: [region],
        ),
    )
    queries = ReferenceQueries(atlas, AtlasOutsideMask(), JsonContextualBoundaryRepository(path))
    assert [item.id for item in queries.boundaries()] == ["07000000"]
    contextual = queries.contextual_boundaries()
    assert contextual[0].display_only
    assert not contextual[0].analytics_enabled
    assert contextual[0].contested
    coords = queries.outside_mask(queries.boundaries(), contextual)
    assert coords is not None
    mask = MultiPolygon([Polygon(rings[0], rings[1:]) for rings in coords])
    assert not mask.covers(Point(30.5, 45.5))
    assert not mask.covers(Point(40.5, 44.5))
    assert mask.covers(Point(35, 45))


def test_context_source_cannot_enable_analytical_actions(tmp_path: Path) -> None:
    path = tmp_path / "context.json"
    source(path, display_only=False)
    with pytest.raises(DataUnavailable):
        JsonContextualBoundaryRepository(path).boundaries()
