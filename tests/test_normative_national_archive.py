import json

import pyarrow as pa
import pyarrow.parquet as pq
import pytest
from synthetic_traffic.normative_national_archive import archive_region


def test_region_archive_requires_complete_matching_parquet_counts(tmp_path):
    folder = tmp_path / ".local/normative-regional-walking/networks/region/revision"
    folder.mkdir(parents=True)
    metadata = {
        "revision": "revision",
        "node_count": 2,
        "edge_count": 1,
        "origin_count": 1,
    }
    (folder / "manifest.json").write_text(json.dumps({"metadata": metadata}))
    for name, count in [("nodes", 2), ("edges", 1), ("origins", 1)]:
        pq.write_table(
            pa.table({"id": list(range(count))}), folder / (name + ".parquet")
        )
    result = archive_region(tmp_path, "region")
    assert result["status"] == "complete"
    assert all(len(record["sha256"]) == 64 for record in result["files"].values())
    assert not any(
        record["path"].startswith("/") for record in result["files"].values()
    )
    (folder / "artifacts.json").unlink()
    pq.write_table(pa.table({"id": []}), folder / "edges.parquet")
    with pytest.raises(ValueError, match="published count"):
        archive_region(tmp_path, "region")
    assert not (folder / "artifacts.json").exists()
