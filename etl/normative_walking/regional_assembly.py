from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq


def tables(paths: list[Path], kind: str) -> pa.Table:
    files = [path / (kind + '.parquet') for path in paths if (path / (kind + '.parquet')).exists()]
    if not files:
        raise ValueError('No regional walking ' + kind + ' records')
    return pa.concat_tables([pq.read_table(path) for path in files])


def groups(keys: np.ndarray) -> np.ndarray:
    return np.flatnonzero(np.r_[True, keys[1:] != keys[:-1]]) if len(keys) else np.array([], dtype=np.int64)


def write_table(path: Path, revision: str, columns: dict[str, object], schema: pa.Schema) -> None:
    length = len(next(iter(columns.values())))
    with pq.ParquetWriter(path, schema) as writer:
        for start in range(0, length, 100000):
            end = min(start + 100000, length)
            data = {key: value[start:end] for key, value in columns.items()}
            data['revision'] = [revision] * (end - start)
            writer.write_table(pa.Table.from_pydict(data, schema=schema))


def assemble(paths: list[Path], output: Path, revision: str) -> dict:
    raw_nodes = tables(paths, 'nodes')
    ids = raw_nodes['osm_id'].to_numpy()
    order = np.argsort(ids, kind='stable')
    ids = ids[order]
    starts = groups(ids)
    latitude = raw_nodes['latitude'].to_numpy()[order]
    longitude = raw_nodes['longitude'].to_numpy()[order]
    valid = ((np.maximum.reduceat(latitude, starts) - np.minimum.reduceat(latitude, starts) < 1e-7)
             & (np.maximum.reduceat(longitude, starts) - np.minimum.reduceat(longitude, starts) < 1e-7))
    unique_ids, lat, lon = ids[starts][valid], latitude[starts][valid], longitude[starts][valid]
    node_conflicts = int(np.count_nonzero(~valid))
    del raw_nodes, ids, order, latitude, longitude
    nodes_schema = pa.schema([('revision', pa.string()), ('node_index', pa.uint32()), ('osm_id', pa.int64()), ('latitude', pa.float64()), ('longitude', pa.float64())])
    write_table(output / 'nodes.parquet', revision,
                {'node_index': np.arange(len(unique_ids), dtype=np.uint32), 'osm_id': unique_ids, 'latitude': lat, 'longitude': lon}, nodes_schema)
    raw_edges = tables(paths, 'edges')
    source, target = raw_edges['source'].to_numpy(), raw_edges['target'].to_numpy()
    keep = np.isin(source, unique_ids) & np.isin(target, unique_ids)
    source, target = source[keep], target[keep]
    metres, ways = raw_edges['metres'].to_numpy()[keep], raw_edges['way_id'].to_numpy()[keep]
    order = np.lexsort((ways, target, source))
    source, target, metres, ways = source[order], target[order], metres[order], ways[order]
    starts = np.flatnonzero(np.r_[True, (source[1:] != source[:-1]) | (target[1:] != target[:-1]) | (ways[1:] != ways[:-1])]) if len(source) else np.array([], dtype=np.int64)
    valid = np.maximum.reduceat(metres, starts) - np.minimum.reduceat(metres, starts) < 0.01
    edge_conflicts = int(np.count_nonzero(~valid))
    chosen = starts[valid]
    edges_schema = pa.schema([('revision', pa.string()), ('way_id', pa.int64()), ('source', pa.uint32()), ('target', pa.uint32()), ('metres', pa.float64())])
    write_table(output / 'edges.parquet', revision,
                {'way_id': ways[chosen], 'source': np.searchsorted(unique_ids, source[chosen]).astype(np.uint32),
                 'target': np.searchsorted(unique_ids, target[chosen]).astype(np.uint32), 'metres': metres[chosen]}, edges_schema)
    edge_count = len(chosen)
    del raw_edges, source, target, metres, ways, order, starts
    homes = tables(paths, 'origins')
    order = np.argsort(homes['id'].to_numpy(), kind='stable')
    homes = homes.take(pa.array(order))
    starts = groups(homes['id'].to_numpy())
    latitude, longitude = homes['latitude'].to_numpy(), homes['longitude'].to_numpy()
    valid = ((np.maximum.reduceat(latitude, starts) - np.minimum.reduceat(latitude, starts) < 1e-7)
             & (np.maximum.reduceat(longitude, starts) - np.minimum.reduceat(longitude, starts) < 1e-7))
    origin_conflicts = int(np.count_nonzero(~valid))
    homes = homes.take(pa.array(starts[valid]))
    origins_schema = pa.schema([('revision', pa.string()), ('id', pa.string()), ('name', pa.string()), ('latitude', pa.float64()), ('longitude', pa.float64()), ('coordinate_source', pa.string()), ('origin_type', pa.string())])
    write_table(output / 'origins.parquet', revision, {key: homes[key] for key in homes.column_names}, origins_schema)
    return {'nodes': len(unique_ids), 'edges': edge_count, 'residential_buildings': len(homes),
            'conflicting_nodes_excluded': node_conflicts, 'conflicting_edges_excluded': edge_conflicts,
            'conflicting_origins_excluded': origin_conflicts}
