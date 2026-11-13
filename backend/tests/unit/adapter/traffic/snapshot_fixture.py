import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq


def snapshot(path: Path) -> None:
    pq.write_table(
        pa.table(
            {
                "src": [10, 20, 20, 30],
                "dst": [20, 10, 30, 20],
                "free_hours": [0.1] * 4,
                "capacity": [1800.0] * 4,
                "km": [5.0] * 4,
                "way_id": [100, 100, 200, 200],
                "shared": [False] * 4,
                "access": [True] * 4,
            }
        ),
        path / "edges.parquet",
    )
    pq.write_table(
        pa.table({"node": [10, 20, 30], "lat": [44.0] * 3, "lon": [42.0, 42.05, 42.1]}),
        path / "nodes.parquet",
    )
    pq.write_table(
        pa.table(
            {
                "point_id": ["a", "b"],
                "settlement": ["A", "B"],
                "region": ["R"] * 2,
                "population": [240000.0] * 2,
                "node": [10, 30],
                "lat": [44.0] * 2,
                "lon": [42.0, 42.1],
            }
        ),
        path / "places.parquet",
    )
    pq.write_table(
        pa.table(
            {
                "id": ["h1", "h2"],
                "lat": [44.0] * 2,
                "lon": [42.0, 42.1],
                "residential_m2_proxy": [100.0] * 2,
            }
        ),
        path / "housing.parquet",
    )
    (path / "source.json").write_text(json.dumps({"sha256": {"edges": "fixture"}}))
