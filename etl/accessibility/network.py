from graphlib import build_csr

import numpy as np
from app.domain.accessibility import departure_cost
from market_distances import market_distances
from scipy.sparse.csgraph import floyd_warshall


def ferry_edges(edges, ways, count, without_water):
    ferry_ids = ways.loc[ways.is_ferry.fillna(False), "way_idx"].to_numpy()
    ferry = edges[edges.way_idx.isin(ferry_ids)]
    road = edges[~edges.way_idx.isin(ferry_ids)]
    src = [road.src.to_numpy(), road.dst.to_numpy()]
    dst = [road.dst.to_numpy(), road.src.to_numpy()]
    weights = [road.h.to_numpy(), road.h.to_numpy()]
    if without_water:
        return src, dst, weights, count
    pairs = sorted(
        set(zip(ferry.way_idx, ferry.src)) | set(zip(ferry.way_idx, ferry.dst))
    )
    nodes = {pair: count + i for i, pair in enumerate(pairs)}
    src.extend([np.array([p[1] for p in pairs]), np.array(list(nodes.values()))])
    dst.extend([np.array(list(nodes.values())), np.array([p[1] for p in pairs])])
    weights.extend(
        [
            np.full(len(pairs), departure_cost(0, "ferry", None).planned_hours),
            np.zeros(len(pairs)),
        ]
    )
    a = np.array([nodes[p] for p in zip(ferry.way_idx, ferry.src)])
    b = np.array([nodes[p] for p in zip(ferry.way_idx, ferry.dst)])
    src.extend([a, b])
    dst.extend([b, a])
    weights.extend([ferry.h.to_numpy()] * 2)
    return src, dst, weights, count + len(pairs)


def local_matrix(source, season, removed, workers):
    edges, ways = source.graph()
    points = source.points.copy()
    cities = source.cities
    count = int(max(edges.src.max(), edges.dst.max(), cities.node.max()) + 1)
    src, dst, weights, count = ferry_edges(edges, ways, count, removed == "water")
    selected = source.manual[source.manual.season == season]
    excluded = (
        ["air"]
        if removed == "air"
        else ["river", "ferry"]
        if removed == "water"
        else []
    )
    selected = selected[~selected["mode"].isin(excluded)]
    linked = points.point_id.isin(set(selected.from_id) | set(selected.to_id))
    missing = (points.node < 0) & linked
    points.loc[missing, "node"] = count + np.arange(missing.sum())
    points.loc[missing, "snap_h"] = 0.0
    count += int(missing.sum())
    lookup = points.set_index("point_id")
    ms, md, mw = [], [], []
    for row in selected.itertuples():
        if row.from_id not in lookup.index or row.to_id not in lookup.index:
            continue
        a, b = lookup.loc[row.from_id], lookup.loc[row.to_id]
        if a.node < 0 or b.node < 0:
            continue
        cost = departure_cost(float(row.travel_h), row.mode, None, terminal_hours=0)
        ms.extend([int(a.node), int(b.node)])
        md.extend([int(b.node), int(a.node)])
        mw.extend([cost.planned_hours + a.snap_h + b.snap_h] * 2)
    src.append(np.asarray(ms))
    dst.append(np.asarray(md))
    weights.append(np.asarray(mw))
    graph = build_csr(
        np.concatenate(src).astype(np.int64),
        np.concatenate(dst).astype(np.int64),
        np.concatenate(weights),
        count,
    ).astype(np.float64)
    connected = points.node >= 0
    distances, city_roads = market_distances(
        graph.T.tocsr(),
        cities.node.to_numpy(dtype=np.int64),
        points.loc[connected, "node"].to_numpy(dtype=np.int64),
        workers,
    )
    road = np.full((len(points), len(cities)), np.inf, dtype=np.float32)
    road[connected] = (
        distances.T
        + points.loc[connected, "snap_h"].to_numpy()[:, None]
        + cities.snap_h.to_numpy()
    )
    city_roads = (
        city_roads.T
        + cities.snap_h.to_numpy()[:, None]
        + cities.snap_h.to_numpy()[None, :]
    )
    return road, city_roads


def best_times(source, road, city_roads, removed=None):
    matrix = city_roads.copy()
    positions = {name: i for i, name in enumerate(source.cities.city)}
    for row in source.trunk.itertuples():
        if row.transport_type == removed:
            continue
        a, b = positions[row.city_from], positions[row.city_to]
        hours = departure_cost(
            float(row.distance_hr), row.transport_type, None
        ).planned_hours
        matrix[a, b] = min(matrix[a, b], hours)
    np.fill_diagonal(matrix, 0.0)
    transfers = floyd_warshall(matrix)
    best = np.empty(road.shape, dtype=np.float64)
    roads = road.astype(np.float64)
    for j in range(len(matrix)):
        best[:, j] = np.min(roads + transfers[:, j], axis=1)
    return best
