import hashlib
import json
import shutil
import sqlite3

import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from synthetic_traffic import geography_tile, geography_tile_sources
from synthetic_traffic.geography import RasterGeography


def surface(lon=0.0):
    return RasterGeography(
        lon,
        0,
        0.001,
        np.ones((3, 3)),
        np.zeros((3, 3), bool),
        np.zeros((3, 3), bool),
        {
            key: "test fixture"
            for key in ("elevation", "water", "buildings", "protected")
        },
    )


def dem(path, missing=False):
    data = np.arange(25, dtype=np.float32).reshape(5, 5)
    if missing:
        data[2, 2] = -9999
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=5,
        height=5,
        count=1,
        dtype="float32",
        crs="EPSG:4326",
        transform=from_origin(0.0005, 0.0055, 0.001, 0.001),
        nodata=-9999,
    ) as destination:
        destination.write(data, 1)
    return data


def test_npz_roundtrip_preserves_arrays_and_metadata(tmp_path):
    original = surface()
    original.blocked[1, 1] = True
    original.water[2, 1] = True
    path = tmp_path / "geography.npz"
    original.save(path)
    restored = RasterGeography.load(path)
    np.testing.assert_array_equal(restored.blocked, original.blocked)
    np.testing.assert_array_equal(restored.water, original.water)
    np.testing.assert_array_equal(restored.elevation_m, original.elevation_m)
    assert restored.elevation_m.dtype == np.float32
    assert restored.sources == original.sources
    assert not list(tmp_path.glob("*.tmp"))


def test_catalog_crops_tiles_and_blocks_uncovered_cells(tmp_path):
    surface().save(tmp_path / "left.npz")
    right = surface(0.002)
    right.blocked[:, 0] = True
    right.save(tmp_path / "right.npz")
    (tmp_path / "unrelated.npz").write_bytes(b"not loaded")
    (tmp_path / "catalog.json").write_text(
        json.dumps(
            {
                "tiles": [
                    {"path": "left.npz", "bbox": [0, 0, 0.002, 0.002]},
                    {"path": "right.npz", "bbox": [0.002, 0, 0.004, 0.002]},
                    {"path": "unrelated.npz", "bbox": [100, 50, 101, 51]},
                ]
            }
        )
    )
    value = RasterGeography.load(tmp_path, bounds=[0, 0, 0.005, 0.002])
    assert value.blocked.shape == (3, 6)
    assert value.blocked[:, 2].all()
    assert value.blocked[:, 5].all()
    assert not value.blocked[:, 0].any()
    assert value.sources["coverage"]["uncovered_blocked_cells"] == 3
    with pytest.raises(ValueError, match="selected bounds"):
        RasterGeography.load(tmp_path)


def test_catalog_rejects_misaligned_tile_grid(tmp_path):
    surface().save(tmp_path / "left.npz")
    surface(0.0025).save(tmp_path / "right.npz")
    (tmp_path / "catalog.json").write_text(
        json.dumps(
            {
                "tiles": [
                    {"path": "left.npz", "bbox": [0, 0, 0.002, 0.002]},
                    {"path": "right.npz", "bbox": [0.0025, 0, 0.0045, 0.002]},
                ]
            }
        )
    )
    with pytest.raises(ValueError, match="aligned"):
        RasterGeography.load(tmp_path, bounds=[0, 0, 0.004, 0.002])


def test_fetch_reprojects_grid_without_point_sampling_and_publishes_hash(
    tmp_path, monkeypatch
):
    source = tmp_path / "source.tif"
    expected = dem(source)
    monkeypatch.setattr(
        geography_tile,
        "_dem",
        lambda *args: (source, {"url": "test://dem", "sha256": "source fixture"}),
    )
    monkeypatch.setattr(
        geography_tile,
        "_vectors",
        lambda *args: (
            {key: [] for key in ("water", "buildings", "protected")},
            {"provider": "test fixture"},
        ),
    )
    output = tmp_path / "tile"
    manifest = geography_tile.fetch_tile(
        [0.001, 0.001, 0.005, 0.005], output, tmp_path / "cache"
    )
    assert manifest["status"] == "complete"
    assert (
        manifest["sha256"]
        == hashlib.sha256((output / "geography.npz").read_bytes()).hexdigest()
    )
    np.testing.assert_array_equal(
        RasterGeography.load(output / "geography.npz").elevation_m, expected[::-1]
    )
    assert not list(output.glob("raw-*"))
    assert not list(output.glob("*.tmp"))


def test_fetch_nodata_never_publishes_a_clear_tile(tmp_path, monkeypatch):
    source = tmp_path / "source.tif"
    dem(source, missing=True)
    monkeypatch.setattr(
        geography_tile, "_dem", lambda *args: (source, {"url": "test://dem"})
    )
    monkeypatch.setattr(
        geography_tile,
        "_vectors",
        lambda *args: ({key: [] for key in ("water", "buildings", "protected")}, {}),
    )
    output = tmp_path / "tile"
    with pytest.raises(ValueError, match="nodata"):
        geography_tile.fetch_tile(
            [0.001, 0.001, 0.005, 0.005], output, tmp_path / "cache"
        )
    assert not (output / "geography.npz").exists()
    assert not (output / "manifest.json").exists()
    assert not list(output.glob("raw-*"))


def test_dem_cache_reuses_url_content_and_checks_checksum(tmp_path, monkeypatch):
    source = tmp_path / "source.tif"
    dem(source)
    calls = []

    def download(url, destination):
        calls.append(url)
        shutil.copyfile(source, destination)
        return {
            "url": url,
            "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
            "bytes": source.stat().st_size,
        }

    monkeypatch.setattr(geography_tile_sources, "download", download)
    first, _ = geography_tile_sources._dem(44, 43, tmp_path / "cache")
    second, _ = geography_tile_sources._dem(44, 43, tmp_path / "cache")
    assert first == second
    assert len(calls) == 1
    first.write_bytes(b"corrupted")
    geography_tile_sources._dem(44, 43, tmp_path / "cache")
    assert len(calls) == 2


@pytest.mark.parametrize(
    "coverage,uses_cache",
    [
        (None, False),
        (
            {
                "type": "Polygon",
                "coordinates": [
                    [[0, 0], [1, 0], [1, 0.4], [0.4, 0.4], [0.4, 1], [0, 1], [0, 0]]
                ],
            },
            False,
        ),
        (
            {
                "type": "Polygon",
                "coordinates": [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]],
            },
            True,
        ),
    ],
)
def test_pbf_requires_exact_polygon_coverage_before_using_empty_masks(
    tmp_path, monkeypatch, coverage, uses_cache
):
    cache = tmp_path / "vectors.sqlite"
    with sqlite3.connect(cache) as connection:
        connection.execute("CREATE TABLE metadata (key TEXT, value TEXT)")
        connection.execute(
            "INSERT INTO metadata VALUES (?, ?)",
            (
                "manifest",
                json.dumps({"coverage_geometry": coverage, "bounds": [0, 0, 1, 1]}),
            ),
        )
    called = []

    def query(*args, **kwargs):
        called.append("pbf")
        return {key: [] for key in ("water", "buildings", "protected")}

    def download(url, destination, body):
        called.append("overpass")
        destination.write_text(json.dumps({"elements": []}))
        return {"url": url, "sha256": "test fixture"}

    monkeypatch.setattr(geography_tile_sources, "query_vector_cache", query)
    monkeypatch.setattr(geography_tile_sources, "download", download)
    _, record = geography_tile_sources._vectors(
        [0.6, 0.6, 0.8, 0.8], 0.001, tmp_path, cache
    )
    assert called == (["pbf"] if uses_cache else ["overpass"])
    if not uses_cache:
        assert "vector_cache_fallback" in record
