from dataclasses import dataclass
from math import isfinite

import numpy as np
from numpy.typing import NDArray


@dataclass(frozen=True)
class Zone:
    id: str
    node: int
    population: float
    lat: float
    lon: float


@dataclass(frozen=True)
class Trip:
    origin: int
    destination: int
    vehicles_per_hour: float


@dataclass(frozen=True)
class DemandParameters:
    daily_person_trips: float = 2.0
    interzonal_share: float = 0.25
    car_share: float = 0.5
    car_occupancy: float = 1.5
    hour_share: float = 0.1
    half_life_hours: float = 1.0
    max_trip_hours: float = 4.0

    def __post_init__(self) -> None:
        values = list(vars(self).values())
        if any(not isfinite(v) or v <= 0 for v in values):
            raise ValueError("Demand parameters must be finite and positive")
        if any(v > 1 for v in [self.interzonal_share, self.car_share, self.hour_share]):
            raise ValueError("Demand shares cannot exceed one")
        if self.car_occupancy < 1:
            raise ValueError("Car occupancy must be at least one")

    def production(self, population: float) -> float:
        return (
            population
            * self.daily_person_trips
            * self.interzonal_share
            * self.car_share
            * self.hour_share
            / self.car_occupancy
        )


@dataclass
class Network:
    source: NDArray[np.int64]
    target: NDArray[np.int64]
    free_hours: NDArray[np.float64]
    capacity: NDArray[np.float64]
    length_km: NDArray[np.float64]
    way_id: NDArray[np.int64]
    raw_nodes: NDArray[np.int64]
    lat: NDArray[np.float64]
    lon: NDArray[np.float64]
    shared: NDArray[np.int64]
    access_raw_nodes: NDArray[np.int64] | None = None
    geometries: dict[int, list[list[float]]] | None = None

    def __post_init__(self) -> None:
        count = len(self.source)
        if not count or any(
            len(a) != count
            for a in [
                self.target,
                self.free_hours,
                self.capacity,
                self.length_km,
                self.way_id,
                self.shared,
            ]
        ):
            raise ValueError("Network edge arrays must be nonempty and aligned")
        for a in [self.free_hours, self.capacity, self.length_km]:
            if np.any(~np.isfinite(a)) or np.any(a <= 0):
                raise ValueError(
                    "Network times, capacities and lengths must be positive"
                )
        if (
            self.source.min() < 0
            or self.target.min() < 0
            or max(self.source.max(), self.target.max()) >= len(self.raw_nodes)
        ):
            raise ValueError("Edge endpoint is outside the network")
        if len(self.lat) != len(self.raw_nodes) or len(self.lon) != len(self.raw_nodes):
            raise ValueError("Node coordinates must align with node identifiers")
        if (
            np.any(~np.isfinite(self.lat))
            or np.any(~np.isfinite(self.lon))
            or np.any(np.abs(self.lat) > 90)
            or np.any(np.abs(self.lon) > 180)
        ):
            raise ValueError("Node coordinates must be finite geographic coordinates")
        if len(np.unique(self.raw_nodes)) != len(self.raw_nodes):
            raise ValueError("Node identifiers must be unique")
