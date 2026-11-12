import json
from hashlib import sha256
from pathlib import Path

import numpy as np
import osmium
import pyarrow as pa
import pyarrow.parquet as pq
from pyproj import Geod
from shapely.geometry import shape

RESIDENTIAL = {
    "residential",
    "house",
    "apartments",
    "detached",
    "semidetached_house",
    "terrace",
    "dormitory",
    "bungalow",
}


class Houses(osmium.SimpleHandler):
    def __init__(self, destination: Path) -> None:
        super().__init__()
        self.factory = osmium.geom.GeoJSONFactory()
        self.geod = Geod(ellps="WGS84")
        self.destination = destination
        self.writer: pq.ParquetWriter | None = None
        self.rows: list[dict] = []
        self.count = 0
        self.skipped = 0
        self.unknown_floors = 0

    def area(self, area: osmium.osm.Area) -> None:
        kind = area.tags.get("building", "")
        if kind not in RESIDENTIAL:
            return
        if any(
            area.tags.get(key, "") in {"yes", "true", "1"}
            for key in ["abandoned", "disused"]
        ):
            return
        try:
            geometry = shape(json.loads(self.factory.create_multipolygon(area)))
            square_meters = abs(self.geod.geometry_area_perimeter(geometry)[0])
            floors = float(area.tags.get("building:levels", "1"))
            if not np.isfinite(floors) or not 1 <= floors <= 150 or square_meters <= 0:
                raise ValueError("Invalid residential dimensions")
            self.unknown_floors += int("building:levels" not in area.tags)
            center = geometry.representative_point()
            self.rows.append(
                {
                    "id": str(area.id),
                    "lat": center.y,
                    "lon": center.x,
                    "residential_m2_proxy": square_meters * floors,
                    "floors_assumed": "building:levels" not in area.tags,
                }
            )
            self.count += 1
            if len(self.rows) >= 10000:
                self.flush()
        except (ValueError, RuntimeError):
            self.skipped += 1

    def flush(self) -> None:
        if not self.rows:
            return
        table = pa.Table.from_pylist(self.rows)
        if self.writer is None:
            self.writer = pq.ParquetWriter(self.destination, table.schema)
        self.writer.write_table(table)
        self.rows.clear()


def extract(source: Path, destination: Path) -> dict[str, int]:
    if destination.exists():
        raise ValueError("Residential output exists; choose a new output path")
    destination.parent.mkdir(parents=True, exist_ok=True)
    handler = Houses(destination)
    try:
        handler.apply_file(str(source), locations=True)
        handler.flush()
    finally:
        if handler.writer is not None:
            handler.writer.close()
    if handler.count == 0:
        raise ValueError("No explicitly residential buildings found in the source")
    result = {
        "residential_buildings": handler.count,
        "invalid_geometry_or_floors": handler.skipped,
        "buildings_with_assumed_one_floor": handler.unknown_floors,
    }
    destination.with_suffix(".json").write_text(
        json.dumps(
            {
                **result,
                "pbf_sha256": sha256(source.read_bytes()).hexdigest(),
                "source_path": str(source),
                "residential_type_filter": sorted(RESIDENTIAL),
                "unknown_floors": "one_assumed",
                "population": "not_observed_in_buildings",
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return result
