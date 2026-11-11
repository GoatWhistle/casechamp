import os

import numpy as np
import pyarrow as pa
from app.adapter.road_graph.data import GraphData
from app.adapter.road_graph.routing import GraphRouting
from app.adapter.road_graph.shortest_paths import ShortestPaths
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.graph_snapshot import ClickHouseGraphSnapshot

from .metrics import network_efficiency, point_metrics
from .network import local_times, network, road_matrix
from .storage import mapped

CASE = "plexus_capacity_casechamp"


class CandidateReader(ClickHouseReader):
    def rows(self, sql, parameters):
        return super().rows(mapped(sql), parameters)

    def arrow(self, sql, parameters):
        return super().arrow(mapped(sql), parameters)


class LegacyCapacitySnapshot(ClickHouseGraphSnapshot):
    def __init__(self, reader, revision):
        super().__init__(reader)
        self._lane_revision = revision

    @property
    def revision(self):
        return self._lane_revision

    def read(self, query, parameters=None):
        if query == "model_version":
            return []
        return super().read(query, parameters)


def insert_frame(store, table, frame):
    fields = [row["name"] for row in store.rows(f"DESCRIBE TABLE {table}")]
    missing = set(fields) - set(frame.columns)
    if missing:
        raise ValueError(f"Missing output fields: {table}: {missing}")
    values = pa.Table.from_pandas(frame[fields], preserve_index=False)
    store.insert_arrow(table, values)


def update_access(origins, road, best, cities, local, capital):
    result = origins.copy()
    for name in [
        "t_district_center_h",
        "t_centre_1k_h",
        "t_centre_5k_h",
        "t_centre_18k_h",
    ]:
        result[name] = local[name]
    nearest = np.argmin(road, axis=1)
    result["nearest_city"] = [
        cities[index][0] if np.isfinite(road[row]).any() else None
        for row, index in enumerate(nearest)
    ]
    result["t_nearest_city_h"] = road[np.arange(len(road)), nearest]
    result["t_capital_h"] = road[:, capital] if capital is not None else np.nan
    result["t_capital_best_h"] = best[:, capital] if capital is not None else np.nan
    for column in ["t_nearest_city_h", "t_capital_h", "t_capital_best_h"]:
        result[column] = result[column].where(np.isfinite(result[column]))
    result["dc_is_own"] = local.get("dc_is_own", result.dc_is_own)
    return result


def rebuild_matrices(store, root, output, reference, revision, workers):
    if not 1 <= workers <= 48:
        raise ValueError("Worker count must be between 1 and 48")
    reader = CandidateReader(
        os.environ["CLICKHOUSE_URL"],
        os.environ.get("CLICKHOUSE_USER", "plexus"),
        os.environ["CLICKHOUSE_PASSWORD"],
    )
    data = GraphData(root / "data", LegacyCapacitySnapshot(reader, revision))
    paths = ShortestPaths(workers)
    routing = GraphRouting(data, paths)
    cities = data.read("cities")
    city_position = {row[0]: index for index, row in enumerate(cities)}
    city_frame = store.frame(
        f"SELECT city,region,is_capital,lat,lon FROM {CASE}.market_cities"
    )
    coordinates = (
        city_frame.set_index("city")
        .loc[[row[0] for row in cities], ["lat", "lon"]]
        .to_numpy(dtype=float)
    )
    capitals = dict(
        zip(
            city_frame.loc[city_frame.is_capital.fillna(False), "region"],
            city_frame.loc[city_frame.is_capital.fillna(False), "city"],
            strict=True,
        )
    )
    capitals["Московская область"] = "Москва"
    destinations = {
        table: store.fresh(f"{CASE}.{table}")
        for table in ["np_city_times", "np_access", "idx_np"]
    }
    results = []
    try:
        for season in ["road", "summer", "winter"]:
            origins = store.frame(
                f"SELECT * FROM {CASE}.reference_idx_np WHERE season='{season}' ORDER BY point_id"
            )
            access = store.frame(
                f"SELECT * FROM {CASE}.reference_np_access WHERE season='{season}' ORDER BY point_id"
            )
            locations = store.frame(
                "SELECT point_id,lat,lon FROM plexus_capacity_graph.locations"
            )
            origins = origins.merge(
                locations, on="point_id", how="left", validate="one_to_one"
            )
            graph, lookup = network(routing, season)
            local = local_times(graph, lookup, origins)
            positions = {identifier: i for i, identifier in enumerate(origins.point_id)}
            del graph
            for region in sorted(origins.region.unique()):
                frame = (
                    origins.loc[origins.region == region]
                    .sort_values("point_id")
                    .reset_index(drop=True)
                )
                captured = {}

                def capture(ids, markets, times, frame=frame, captured=captured):
                    if ids != frame.point_id.tolist() or markets != [
                        row[0] for row in cities
                    ]:
                        raise ValueError("Routing identifiers do not match source rows")
                    captured["best"] = times

                index, *_ = routing.calculate(
                    region, season, [], lambda value: None, on_times=capture
                )
                best = captured["best"]
                road = road_matrix(routing, season, lookup, frame.point_id.tolist())
                selected = np.array(
                    [positions[identifier] for identifier in frame.point_id]
                )
                regional_local = {key: value[selected] for key, value in local.items()}
                metrics = point_metrics(
                    frame, road, best, cities, regional_local, reference
                )
                metrics["net_efficiency"] = network_efficiency(
                    best,
                    frame,
                    coordinates,
                    np.array([row[3] for row in cities], dtype=float),
                )
                cap = city_position.get(capitals.get(region))
                metrics["t_capital_best_h"] = (
                    best[:, cap] if cap is not None else np.nan
                )
                metrics["t_capital_best_h"] = metrics.t_capital_best_h.where(
                    np.isfinite(metrics.t_capital_best_h)
                )
                insert_frame(store, destinations["idx_np"], metrics)
                own_access = (
                    access.loc[access.region == region]
                    .sort_values("point_id")
                    .reset_index(drop=True)
                )
                if own_access.point_id.tolist() != frame.point_id.tolist():
                    raise ValueError("Access origins do not match index origins")
                insert_frame(
                    store,
                    destinations["np_access"],
                    update_access(own_access, road, best, cities, regional_local, cap),
                )
                i, j = np.nonzero(np.isfinite(best))
                table = pa.table(
                    {
                        "season": [season] * len(i),
                        "point_id": frame.point_id.to_numpy()[i],
                        "city": np.array([row[0] for row in cities])[j],
                        "road_h": road[i, j],
                        "best_h": best[i, j].astype(np.float32),
                    }
                )
                store.insert_arrow(destinations["np_city_times"], table)
                computed = float(
                    metrics.hansen_idx.to_numpy()
                    @ frame.population.fillna(0).to_numpy()
                    / frame.population.fillna(0).sum()
                )
                if not np.isclose(computed, index, rtol=1e-5, atol=1e-4):
                    raise ValueError("Runtime and ETL Hansen disagree")
                results.append(
                    {
                        "season": season,
                        "region": region,
                        "runtime": index,
                        "etl": computed,
                    }
                )
                print(f"capacity {season} {region}: {index:.8f}", flush=True)
        for table, loading in destinations.items():
            store.replace(loading, f"{CASE}.{table}")
    finally:
        paths.close()
    return {
        "baselines": results,
        "regions": len({row["region"] for row in results}),
        "seasons": 3,
    }
