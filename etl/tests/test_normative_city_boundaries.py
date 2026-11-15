import json

from synthetic_traffic import normative_city_boundaries as cities


def test_both_city_counts_and_partial_source_status_are_preserved_atomically(
    tmp_path, monkeypatch
):
    def extract(pbfs, regions, output, levels, region_ids, municipal_only):
        assert levels == (8,)
        assert municipal_only
        count = 1 if region_ids == ["45000000"] else 2
        result = {"features": count, "sources": [{"sha256": "source"}]}
        output.write_text(json.dumps({"features": [{}] * count}))
        output.with_suffix(".manifest.json").write_text(json.dumps(result))
        return result

    monkeypatch.setattr(cities, "extract_municipal_boundaries", extract)
    monkeypatch.setattr(
        cities,
        "import_files",
        lambda paths: {"inserted": len(json.loads(paths[0].read_text())["features"])},
    )
    (tmp_path / ".local/normative-national-inputs").mkdir(parents=True)
    report = cities.prepare_city_boundaries(tmp_path)
    assert [(row["region_id"], row["features"]) for row in report] == [
        ("45000000", 1),
        ("40000000", 2),
    ]
    assert all(row["status"] == "partial_source_coverage" for row in report)
    assert all(row["portable_geometry"].endswith(".geojson") for row in report)
    output = tmp_path / "datasets/municipal-boundaries/federal-cities"
    assert json.loads((output / "import-progress.json").read_text()) == report
    assert not list(output.glob("*.part"))


def test_empty_city_never_imports_or_claims_available_geometry(tmp_path, monkeypatch):
    monkeypatch.setattr(
        cities, "extract_municipal_boundaries", lambda *args: {"features": 0}
    )

    def forbidden(paths):
        raise AssertionError("Empty city must not be imported")

    monkeypatch.setattr(cities, "import_files", forbidden)
    (tmp_path / ".local/normative-national-inputs").mkdir(parents=True)
    report = cities.prepare_city_boundaries(tmp_path)
    assert len(report) == 2
    assert all(row["status"] == "municipal_geometry_unavailable" for row in report)
