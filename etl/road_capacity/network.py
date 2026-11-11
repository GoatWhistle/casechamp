import numpy as np
from app.adapter.road_graph.routing import minimum_csr
from scipy.sparse.csgraph import dijkstra


def network(routing, scenario):
    data = routing.data
    data.load()
    lookup = {row[0]: [int(row[1]), float(row[2]) / 15] for row in data.read("points")}
    count = len(data.nodes["lat"])
    _, manual = routing.networks(scenario)
    for source, target, *_ in manual:
        for point in [source, target]:
            if point in lookup and lookup[point][0] < 0:
                lookup[point] = [count, 0.0]
                count += 1
    ms, md, mw = [], [], []
    for source, target, hours, *_ in manual:
        if source in lookup and target in lookup:
            left, right = lookup[source], lookup[target]
            ms.append(left[0])
            md.append(right[0])
            mw.append(hours + left[1] + right[1])
    edges = data.edges
    graph = minimum_csr(
        np.concatenate([edges["src"], ms]).astype(np.int32),
        np.concatenate([edges["dst"], md]).astype(np.int32),
        np.concatenate([edges["h"], mw]),
        count,
    )
    return graph, lookup


def local_times(graph, lookup, origins):
    nodes = np.array(
        [lookup.get(identifier, [-1, 0])[0] for identifier in origins.point_id],
        dtype=np.int64,
    )
    snaps = np.array(
        [lookup.get(identifier, [-1, 0])[1] for identifier in origins.point_id],
        dtype=float,
    )
    valid = nodes >= 0
    result = {"dc_is_own": np.zeros(len(origins), dtype=bool)}
    district = origins.loc[origins.is_dc.fillna(False)].drop_duplicates(
        ["region", "mun_upper"]
    )
    district_selected = np.zeros(len(origins), dtype=bool)
    district_selected[district.index.to_numpy(dtype=int)] = True
    own_nodes = {
        (str(row.region), str(row.mun_upper)): int(nodes[index])
        for index, row in district.iterrows()
    }
    specs = [
        ("t_district_center_h", district_selected, 24.0),
        *[
            (
                f"t_centre_{threshold // 1000}k_h",
                origins.population.fillna(0).to_numpy() >= threshold,
                np.inf,
            )
            for threshold in [1000, 5000, 18000]
        ],
    ]
    for name, selected, limit in specs:
        source_positions = np.flatnonzero(selected & valid)
        output = np.full(len(origins), np.nan)
        if len(source_positions):
            unique, first = np.unique(nodes[source_positions], return_index=True)
            selected_positions = source_positions[first]
            distances, _, source = dijkstra(
                graph,
                directed=True,
                indices=unique,
                min_only=True,
                return_predecessors=True,
                limit=limit,
            )
            source_snaps = dict(
                zip(unique.tolist(), snaps[selected_positions].tolist(), strict=True)
            )
            reached = source[nodes[valid]]
            values = (
                distances[nodes[valid]]
                + snaps[valid]
                + np.array([source_snaps.get(int(node), 0) for node in reached])
            )
            values[~np.isfinite(values) | (reached < 0)] = np.nan
            output[valid] = values
            if name == "t_district_center_h":
                own = np.array(
                    [
                        own_nodes.get((str(row.region), str(row.mun_upper)), -1)
                        for row in origins.itertuples()
                    ]
                )
                marker = np.zeros(len(origins), dtype=bool)
                marker[valid] = reached == own[valid]
                result["dc_is_own"] = marker
            if name.startswith("t_centre_"):
                output[selected & valid] = 0.0
        result[name] = output
    return result


def road_matrix(routing, scenario, lookup, identifiers):
    cities = routing.data.read("cities")
    city_nodes = np.array([row[1] for row in cities], dtype=np.int64)
    city_snaps = np.array([row[2] for row in cities], dtype=float)
    targets = np.unique(
        np.concatenate(
            [
                np.array([v[0] for v in lookup.values() if v[0] >= 0], dtype=np.int64),
                city_nodes,
            ]
        )
    )
    every = routing.searches.get((scenario, (), ()))
    if every is None:
        raise ValueError("Shared national searches are missing")
    nodes = np.array([lookup.get(identifier, [-1, 0])[0] for identifier in identifiers])
    snaps = np.array([lookup.get(identifier, [-1, 0])[1] for identifier in identifiers])
    matrix = np.full((len(identifiers), len(cities)), np.inf, dtype=np.float32)
    valid = nodes >= 0
    matrix[valid] = (
        every[:, np.searchsorted(targets, nodes[valid])].T.astype(np.float32)
        + snaps[valid, None]
        + city_snaps[None, :]
    )
    return matrix
