from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
from synthetic_traffic.model import Network, Zone


def load_network(source: Path) -> Network:
    table = pq.read_table(source / "edges.parquet")
    arrays = {key: table[key].to_numpy() for key in table.column_names}
    raw = np.unique(np.r_[arrays["src"], arrays["dst"]]).astype(np.int64)
    coordinates = pq.read_table(source / "nodes.parquet")
    order = np.argsort(coordinates["node"].to_numpy())
    ids = coordinates["node"].to_numpy()[order]
    locations = np.searchsorted(ids, raw)
    if np.any(locations >= len(ids)) or not np.array_equal(ids[locations], raw):
        raise ValueError("Snapshot has missing node coordinates")
    shared = np.full(len(arrays["src"]), -1, dtype=np.int64)
    selected = arrays["shared"].astype(bool)
    if selected.any():
        keys = np.column_stack(
            (
                arrays["way_id"][selected],
                np.minimum(arrays["src"][selected], arrays["dst"][selected]),
                np.maximum(arrays["src"][selected], arrays["dst"][selected]),
            )
        )
        _, shared[selected] = np.unique(keys, axis=0, return_inverse=True)
    return Network(
        np.searchsorted(raw, arrays["src"]).astype(np.int64),
        np.searchsorted(raw, arrays["dst"]).astype(np.int64),
        arrays["free_hours"].astype(float),
        arrays["capacity"].astype(float),
        arrays["km"].astype(float),
        arrays["way_id"].astype(np.int64),
        raw,
        coordinates["lat"].to_numpy()[order][locations].astype(float),
        coordinates["lon"].to_numpy()[order][locations].astype(float),
        shared,
        np.unique(
            np.r_[
                arrays["src"][arrays["access"].astype(bool)],
                arrays["dst"][arrays["access"].astype(bool)],
            ]
        ),
    )


def load_places(
    source: Path, network: Network, region: str | list[str] | None = None
) -> tuple[list[Zone], dict]:
    regions = {region} if isinstance(region, str) else set(region or [])
    rows = pq.read_table(source / "places.parquet").to_pylist()
    seen = set()
    zones = []
    missing_population = 0.0
    for row in rows:
        if row["point_id"] in seen or (regions and row["region"] not in regions):
            continue
        seen.add(row["point_id"])
        population = max(0.0, float(row["population"] or 0))
        node = int(row["node"]) if row["node"] is not None else -1
        position = int(np.searchsorted(network.raw_nodes, node))
        if position >= len(network.raw_nodes) or network.raw_nodes[position] != node:
            missing_population += population
            continue
        if population > 0:
            zones.append(
                Zone(
                    str(row["point_id"]),
                    position,
                    population,
                    float(row["lat"]),
                    float(row["lon"]),
                )
            )
    if not zones:
        raise ValueError("No populated, road-bound origins match this scope")
    return zones, {
        "missing_or_outside_network_population": missing_population,
        "settlements": len(zones),
        "region": region,
    }
