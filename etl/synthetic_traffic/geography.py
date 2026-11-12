import json
from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4

import numpy as np
from synthetic_traffic.tile_mosaic import mosaic_payload, read_tile


@dataclass
class RasterGeography:
    origin_lon: float
    origin_lat: float
    cell_degrees: float
    elevation_m: np.ndarray
    blocked: np.ndarray
    water: np.ndarray
    sources: dict
    openings: list[dict] = field(default_factory=list)
    max_grade: float = 0.08
    max_bridge_km: float = 5.0
    max_tunnel_km: float = 20.0

    def __post_init__(self):
        self.elevation_m = np.asarray(self.elevation_m, dtype=np.float32)
        self.blocked = np.asarray(self.blocked, dtype=bool)
        self.water = np.asarray(self.water, dtype=bool)
        if self.elevation_m.ndim != 2 or min(self.elevation_m.shape) < 2:
            raise ValueError("Geography requires a two-dimensional elevation surface")
        if (
            self.blocked.shape != self.elevation_m.shape
            or self.water.shape != self.elevation_m.shape
        ):
            raise ValueError("Geography raster layers must align")
        if not np.isfinite(self.elevation_m).all() or not 0 < self.cell_degrees <= 1:
            raise ValueError(
                "Geography requires finite elevations and positive resolution"
            )
        if not all(
            self.sources.get(key)
            for key in ("elevation", "water", "buildings", "protected")
        ):
            raise ValueError(
                "Geography requires provenance for elevation, water, buildings and protected zones"
            )
        if not all(
            np.isfinite(v) and v > 0
            for v in (self.max_grade, self.max_bridge_km, self.max_tunnel_km)
        ):
            raise ValueError("Engineering constraints must be finite and positive")

    @classmethod
    def load(cls, path, bounds=None):
        path = Path(path)
        return cls(
            **(mosaic_payload(path, bounds) if path.is_dir() else read_tile(path))
        )

    def save(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_name(path.name + "." + uuid4().hex + ".tmp")
        metadata = {
            key: value
            for key, value in vars(self).items()
            if key not in {"elevation_m", "blocked", "water"}
        }
        try:
            with temporary.open("wb") as output:
                np.savez_compressed(
                    output,
                    elevation_m=self.elevation_m.astype(np.float32),
                    blocked=self.blocked,
                    water=self.water,
                    metadata=json.dumps(metadata),
                )
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)

    def cell(self, lon, lat):
        row = round((lat - self.origin_lat) / self.cell_degrees)
        col = round((lon - self.origin_lon) / self.cell_degrees)
        if 0 <= row < self.blocked.shape[0] and 0 <= col < self.blocked.shape[1]:
            return row, col
        return None

    def coordinate(self, cell):
        return [
            self.origin_lon + cell[1] * self.cell_degrees,
            self.origin_lat + cell[0] * self.cell_degrees,
        ]


def polyline_km(coordinates):
    points = np.asarray(coordinates, dtype=float)
    if (
        points.ndim != 2
        or points.shape[1] != 2
        or len(points) < 2
        or not np.isfinite(points).all()
    ):
        raise ValueError("A corridor needs finite longitude/latitude coordinates")
    if np.any(np.abs(points[:, 0]) > 180) or np.any(np.abs(points[:, 1]) > 90):
        raise ValueError("Corridor coordinates must be geographic")
    radians = np.radians(points)
    delta = np.diff(radians, axis=0)
    hav = (
        np.sin(delta[:, 1] / 2) ** 2
        + np.cos(radians[:-1, 1])
        * np.cos(radians[1:, 1])
        * np.sin(delta[:, 0] / 2) ** 2
    )
    return float(np.sum(12742.0176 * np.arcsin(np.sqrt(np.clip(hav, 0, 1)))))
