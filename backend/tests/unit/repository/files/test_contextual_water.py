import json
from pathlib import Path
from types import SimpleNamespace
from typing import cast

from shapely.geometry import MultiPolygon, Point, Polygon

from app.adapter.atlas.outside_mask import AtlasOutsideMask
from app.repository.files.contextual_water import JsonContextualWaterRepository
from app.usecase.interface import AtlasRepository
from app.usecase.reference import ReferenceQueries


def test_real_source_water_opens_mask_without_becoming_analytical_region(tmp_path: Path) -> None:
    path = tmp_path / "water.json"
    path.write_text(
        json.dumps(
            {
                "contextual_water": [
                    {
                        "id": "context-water",
                        "name": "Water",
                        "bounds": [35, 45, 36, 46],
                        "polygons": [[[[35, 45], [36, 45], [36, 46], [35, 46], [35, 45]]]],
                        "source_url": "https://www.openstreetmap.org/relation/1",
                        "observed_at": "2026-01-15",
                        "source_sha256": "abc",
                        "osm_relation_id": 1,
                        "geometry_basis": "original_rings",
                        "display_only": True,
                        "analytics_enabled": False,
                    }
                ]
            }
        )
    )
    atlas = cast(AtlasRepository, SimpleNamespace(regions=list, boundaries=list))
    queries = ReferenceQueries(atlas, AtlasOutsideMask(), water=JsonContextualWaterRepository(path))
    water = queries.contextual_water()
    assert not queries.boundaries()
    assert not water[0].analytics_enabled
    coordinates = queries.outside_mask([], water=water)
    assert coordinates is not None
    mask = MultiPolygon([Polygon(rings[0], rings[1:]) for rings in coordinates])
    assert not mask.covers(Point(35.5, 45.5))
    assert mask.covers(Point(30, 45))
