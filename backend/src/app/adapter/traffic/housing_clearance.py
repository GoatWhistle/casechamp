from pathlib import Path
from typing import Any

import numpy as np
import pyarrow.parquet as pq
from synthetic_traffic.demand import xyz
from synthetic_traffic.model import Network


def clear_connections(candidates: dict[str, Any], network: Network, source: Path) -> dict[str, Any]:
    homes = pq.read_table(source / "housing.parquet").to_pydict()
    coordinates = xyz(np.array(homes["lat"]), np.array(homes["lon"]))
    radius = (np.sqrt(np.array(homes["residential_m2_proxy"]) / np.pi) + 20) / 1000
    candidates["connections_for_review"] = [
        row
        for row in candidates["connections_for_review"]
        if clear_segment(network, row, coordinates, radius)
    ]
    return candidates


def clear_segment(
    network: Network,
    project: dict[str, Any],
    homes: np.ndarray[Any, Any],
    radius: np.ndarray[Any, Any],
) -> bool:
    if not len(homes):
        return False
    indices = np.searchsorted(network.raw_nodes, [project["source_node"], project["target_node"]])
    ends = xyz(network.lat[indices], network.lon[indices])
    vector = ends[1] - ends[0]
    length = float(vector @ vector)
    if length <= 0:
        return False
    fraction = np.clip((homes - ends[0]) @ vector / length, 0, 1)
    distances = np.linalg.norm(homes - (ends[0] + fraction[:, None] * vector), axis=1)
    return bool(np.all(distances > radius))
