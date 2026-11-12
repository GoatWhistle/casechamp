import hashlib
import json
from math import cos, floor, radians

import numpy as np
from scipy.spatial import cKDTree

CELL_DEGREES = 0.009
SETTLED_RADIUS_KM = 1.0
SNAP_MAX_KM = 5.0
METHOD = 'federal-city-building-cells-v1'


def sphere(lat, lon):
    lat, lon = np.deg2rad(lat), np.deg2rad(lon)
    return np.column_stack((np.cos(lat) * np.cos(lon), np.cos(lat) * np.sin(lon), np.sin(lat)))


def chord_km(chord):
    return 2 * 6371.0088 * np.arcsin(np.minimum(1.0, chord / 2))


def apportion(total, weights):
    shares = total * weights / weights.sum()
    whole = np.floor(shares).astype(np.int64)
    rest = total - int(whole.sum())
    whole[np.argsort(-(shares - whole), kind='stable')[:rest]] += 1
    return whole


def rows(client, query):
    return [json.loads(line) for line in client.request(query + ' FORMAT JSONEachRow').splitlines()]


def city_cells(client, index, existing):
    cities = rows(client, "SELECT oktmo,region,population,latitude,longitude FROM plexus_casechamp.stg_settlements "
                          "WHERE object_level='Город федерального значения' AND population>0 AND latitude IS NOT NULL ORDER BY oktmo")
    comps = [row['comp'] for row in rows(client, 'SELECT DISTINCT n.comp AS comp FROM plexus_graph.locations AS l '
                                                 'INNER JOIN plexus_graph.nodes AS n ON n.node=l.node')]
    records, evidence, digest = [], [], hashlib.sha256(METHOD.encode())
    for city in cities:
        region_id, region_name, status = index.locate(city['latitude'], city['longitude'])
        if status != 'spatial_match' or region_name != city['region']:
            evidence.append({'oktmo': city['oktmo'], 'region': city['region'], 'status': 'city_is_not_a_project_territory'})
            continue
        revision = rows(client, "SELECT revision FROM plexus_normative.pedestrian_regions WHERE purpose='physical' "
                                f"AND region_id='{region_id}' ORDER BY published_at DESC LIMIT 1")
        if not revision:
            evidence.append({'oktmo': city['oktmo'], 'region': city['region'], 'status': 'no_physical_building_snapshot'})
            continue
        revision = revision[0]['revision']
        buildings = rows(client, 'SELECT latitude,longitude FROM plexus_normative.pedestrian_origins '
                                 f"WHERE revision='{revision}' ORDER BY id")
        lat = np.array([b['latitude'] for b in buildings])
        lon = np.array([b['longitude'] for b in buildings])
        inside = np.array([index.locate(a, o)[0] == region_id for a, o in zip(lat, lon)], dtype=bool)
        lat, lon = lat[inside], lon[inside]
        settled = [row for row in existing if row['region_id'] == region_id]
        represented = sum(row['population'] or 0 for row in settled if row['source_region'] == city['region'])
        if settled:
            near, _ = cKDTree(sphere(np.array([r['latitude'] for r in settled]), np.array([r['longitude'] for r in settled]))).query(sphere(lat, lon))
            keep = chord_km(near) > SETTLED_RADIUS_KM
            lat, lon = lat[keep], lon[keep]
        residual = int(city['population']) - int(represented)
        if residual <= 0 or not len(lat):
            evidence.append({'oktmo': city['oktmo'], 'region': city['region'], 'status': 'no_residual_population'})
            continue
        step_lon = CELL_DEGREES / cos(radians(float(np.mean(lat))))
        keys = [(floor(a / CELL_DEGREES), floor(o / step_lon)) for a, o in zip(lat, lon)]
        cells = {}
        for key, a, o in zip(keys, lat, lon):
            cells.setdefault(key, []).append((a, o))
        ordered = sorted(cells)
        counts = np.array([len(cells[key]) for key in ordered], dtype=np.float64)
        population = apportion(residual, counts)
        centre = np.array([np.mean(cells[key], axis=0) for key in ordered])
        box = (centre[:, 0].min() - 0.1, centre[:, 0].max() + 0.1, centre[:, 1].min() - 0.2, centre[:, 1].max() + 0.2)
        nodes = rows(client, 'SELECT node,lat,lon FROM plexus_graph.nodes '
                             f'WHERE lat BETWEEN {box[0]} AND {box[1]} AND lon BETWEEN {box[2]} AND {box[3]} '
                             f"AND comp IN ({','.join(str(c) for c in comps)}) ORDER BY node")
        tree = cKDTree(sphere(np.array([n['lat'] for n in nodes]), np.array([n['lon'] for n in nodes])))
        chord, found = tree.query(sphere(centre[:, 0], centre[:, 1]))
        snap = chord_km(chord)
        for i, key in enumerate(ordered):
            if population[i] <= 0:
                continue
            attached = bool(snap[i] <= SNAP_MAX_KM)
            records.append({'region_id': region_id, 'id': f"{city['oktmo']}-c{key[0]}-{key[1]}",
                            'name': f"{city['region']}, расчётная ячейка {i + 1}", 'population': int(population[i]),
                            'node': int(nodes[int(found[i])]['node']) if attached else None,
                            'snap_km': float(snap[i]) if attached else None,
                            'latitude': float(centre[i, 0]), 'longitude': float(centre[i, 1]),
                            'source_region': city['region']})
        digest.update(json.dumps([city, revision, residual, len(ordered)], sort_keys=True).encode())
        evidence.append({'oktmo': city['oktmo'], 'region': city['region'], 'region_id': region_id,
                         'source_population': city['population'], 'already_represented': represented,
                         'distributed_population': residual, 'building_snapshot': revision,
                         'buildings_used': int(len(lat)), 'cells': len(ordered),
                         'unattached_cells': int(np.sum(snap > SNAP_MAX_KM)), 'status': 'distributed'})
    return records, evidence, digest.hexdigest()
