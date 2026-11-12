import numpy as np
from synthetic_traffic.geography import polyline_km
from synthetic_traffic.model import Network, Trip


def scenario(seed: int) -> tuple[Network, list[Trip], list[dict]]:
    rng = np.random.default_rng(seed)
    size = 9
    pairs = [(i, i + 1) for i in range(size - 1)] + [(0, 4), (4, 8), (2, 6)]
    source = np.asarray([a for a, b in pairs] + [b for a, b in pairs], dtype=np.int64)
    target = np.asarray([b for a, b in pairs] + [a for a, b in pairs], dtype=np.int64)
    scale = rng.uniform(0.008, 0.09)
    lat = 55 + np.arange(size) // 3 * scale
    lon = 37 + np.arange(size) % 3 * scale
    length = np.array(
        [polyline_km([[lon[a], lat[a]], [lon[b], lat[b]]]) for a, b in pairs]
    ) * rng.uniform(1.05, 1.8, len(pairs))
    length = np.r_[length, length]
    speed = rng.uniform(25, 60, len(pairs))
    speed = np.r_[speed, speed]
    capacity = rng.choice([400.0, 800.0, 1800.0], len(pairs))
    capacity = np.r_[capacity, capacity]
    network = Network(
        source,
        target,
        length / speed,
        capacity,
        length,
        np.tile(np.arange(1, len(pairs) + 1), 2),
        np.arange(size),
        lat,
        lon,
        np.full(len(source), -1, dtype=np.int64),
    )
    trips = [
        Trip(int(a), int(b), float(rng.uniform(30, 250)))
        for a, b in rng.integers(0, size, (18, 2))
        if a != b
    ]
    projects = [
        {"kind": kind, "way_ids": [way]}
        for way in range(1, len(pairs) + 1)
        for kind in ("capacity", "closure")
    ]
    for a, b in [
        (0, 3),
        (3, 6),
        (5, 8),
        (0, 8),
        (1, 7),
        (2, 6),
        (1, 5),
        (0, 5),
        (3, 8),
    ]:
        coordinates = [[float(network.lon[i]), float(network.lat[i])] for i in (a, b)]
        projects.append(
            {
                "kind": "connection",
                "source_node": a,
                "target_node": b,
                "length_km": polyline_km(coordinates),
                "speed_kmh": float(rng.choice([35, 45, 60])),
                "capacity_vph": float(rng.choice([800, 1800, 3000])),
                "geometry": {"type": "LineString", "coordinates": coordinates},
            }
        )
    projects.extend(
        {"kind": "capacity", "way_ids": [way], "extra_lanes": 2} for way in (1, 4, 7)
    )
    projects.extend(
        {
            "kind": "package",
            "projects": [
                {"kind": "capacity", "way_ids": [a]},
                {"kind": "capacity", "way_ids": [b]},
            ],
        }
        for a, b in [(1, 4), (2, 7), (5, 10)]
    )
    connections = [p for p in projects if p["kind"] == "connection"]
    projects.extend(
        {"kind": "package", "projects": [connections[a], connections[b]]}
        for a, b in [(0, 3), (1, 5), (2, 4), (6, 8)]
    )
    projects.extend(
        {"kind": "package", "projects": [p, {"kind": "capacity", "way_ids": [i + 1]}]}
        for i, p in enumerate(connections[:4])
    )
    return network, trips, projects
