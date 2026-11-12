from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
from scipy.spatial import cKDTree
from synthetic_traffic.demand import xyz
from synthetic_traffic.model import Network, Zone


def distribute(
    houses: Path,
    settlements: list[Zone],
    network: Network,
    max_settlement_km: float = 5.0,
    max_road_km: float = 1.0,
) -> tuple[list[Zone], dict[str, float]]:
    if not settlements:
        raise ValueError("Housing allocation needs settlements with known population")
    files = sorted(houses.glob("*.parquet")) if houses.is_dir() else houses
    lat = [z.lat for z in settlements]
    lon = [z.lon for z in settlements]
    filters = [
        ("lat", ">=", min(lat) - max_settlement_km / 111),
        ("lat", "<=", max(lat) + max_settlement_km / 111),
    ]
    if max(lon) - min(lon) < 180:
        margin = max_settlement_km / (
            111 * max(0.01, np.cos(np.radians(max(map(abs, lat)))))
        )
        filters += [("lon", ">=", min(lon) - margin), ("lon", "<=", max(lon) + margin)]
    data = pq.read_table(files, filters=filters)
    ids = data["id"].to_numpy()
    _, unique = np.unique(ids, return_index=True)
    duplicate_count = len(ids) - len(unique)
    table = data.take(np.sort(unique)).to_pydict()
    if not table["id"]:
        return settlements, {
            "allocated_population": 0.0,
            "fallback_settlement_population": sum(z.population for z in settlements),
            "used_buildings": 0,
            "unused_buildings": 0,
            "duplicates_removed": duplicate_count,
            "nearest_access_unverified": True,
        }
    coords = xyz(np.array(table["lat"]), np.array(table["lon"]))
    home_tree = cKDTree(
        xyz(
            np.array([z.lat for z in settlements]),
            np.array([z.lon for z in settlements]),
        )
    )
    distance, places = home_tree.query(coords)
    access = (
        np.searchsorted(network.raw_nodes, network.access_raw_nodes)
        if network.access_raw_nodes is not None
        else np.arange(len(network.raw_nodes))
    )
    if len(access) == 0:
        raise ValueError("No local road access nodes available for residential demand")
    road_tree = cKDTree(xyz(network.lat[access], network.lon[access]))
    road_distance, nodes = road_tree.query(coords)
    nodes = access[nodes]
    eligible = (distance <= max_settlement_km) & (road_distance <= max_road_km)
    weights = np.array(table["residential_m2_proxy"], dtype=float)
    if np.any(~np.isfinite(weights)) or np.any(weights <= 0):
        raise ValueError("Housing weights must be finite and positive")
    totals = np.bincount(
        places[eligible], weights=weights[eligible], minlength=len(settlements)
    )
    result = []
    allocated = 0.0
    for index in np.flatnonzero(eligible):
        settlement = settlements[int(places[index])]
        population = settlement.population * weights[index] / totals[places[index]]
        result.append(
            Zone(
                "home-" + str(table["id"][index]),
                int(nodes[index]),
                population,
                float(table["lat"][index]),
                float(table["lon"][index]),
            )
        )
        allocated += population
    fallback = [zone for index, zone in enumerate(settlements) if totals[index] == 0]
    return result + fallback, {
        "allocated_population": allocated,
        "fallback_settlement_population": sum(z.population for z in fallback),
        "used_buildings": int(eligible.sum()),
        "unused_buildings": int((~eligible).sum()),
        "nearest_access_unverified": True,
        "duplicates_removed": duplicate_count,
    }
