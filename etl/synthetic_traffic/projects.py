from dataclasses import replace

import numpy as np
from scipy.sparse import csr_matrix
from scipy.sparse.csgraph import connected_components
from synthetic_traffic.alignment import prepare_alignment
from synthetic_traffic.demand import xyz
from synthetic_traffic.geography import RasterGeography, polyline_km
from synthetic_traffic.model import Network


def apply_project(network: Network, project: dict) -> Network:
    kind = project.get("kind")
    if kind not in {"package", "capacity", "connection", "opening", "closure"}:
        raise ValueError(
            "Project kind must be capacity, connection, opening, closure or package"
        )
    if kind == "package":
        projects = project.get("projects", [])
        if not projects:
            raise ValueError("A package needs projects")
        occupied = set()
        connections = set()
        for item in projects:
            ways = set(item.get("way_ids", []))
            if occupied & ways:
                raise ValueError("Package projects cannot modify the same road twice")
            occupied |= ways
            if item.get("kind") in {"connection", "opening"}:
                pair = tuple(sorted((item["source_node"], item["target_node"])))
                if pair in connections:
                    raise ValueError("Package cannot duplicate the same connection")
                connections.add(pair)
            network = apply_project(network, item)
        return network
    if kind in {"connection", "opening"}:
        nodes = [int(project["source_node"]), int(project["target_node"])]
        positions = np.searchsorted(network.raw_nodes, nodes)
        if np.any(positions >= len(network.raw_nodes)) or not np.array_equal(
            network.raw_nodes[positions], nodes
        ):
            raise ValueError("New connection endpoints are absent from the network")
        a, b = map(int, positions)
        geometry = project.get("geometry")
        if kind == "opening" and not project.get("source_reference"):
            raise ValueError("Opening a road requires its source reference")
        length = float(project["length_km"])
        if geometry is None:
            raise ValueError("A connection requires its routed polyline geometry")
        if geometry is not None:
            if geometry.get("type") != "LineString":
                raise ValueError("Connection geometry must be a LineString")
            coordinates = geometry.get("coordinates", [])
            measured = polyline_km(coordinates)
            endpoints = [
                [float(network.lon[a]), float(network.lat[a])],
                [float(network.lon[b]), float(network.lat[b])],
            ]
            if not np.allclose(
                [coordinates[0], coordinates[-1]], endpoints, rtol=0, atol=1e-7
            ):
                raise ValueError("Corridor geometry must end at its network endpoints")
            if not np.isclose(length, measured, rtol=0.005, atol=0.001):
                raise ValueError("Corridor length must equal its polyline length")
            length = measured
        speed = float(project.get("speed_kmh", 40))
        coords = xyz(network.lat[positions], network.lon[positions])
        chord = float(np.linalg.norm(coords[0] - coords[1]))
        distance = 2 * 6371.0088 * np.arcsin(min(1, chord / (2 * 6371.0088)))
        if a == b or not np.isfinite(length) or not distance - 1e-6 <= length:
            raise ValueError("Connection must be at least its geodesic distance")
        if not np.isfinite(speed) or not 0 < speed <= 140:
            raise ValueError("Connection speed must be in (0,140] km/h")
        capacity = float(project.get("capacity_vph", 1800.0))
        if not np.isfinite(capacity) or capacity <= 0:
            raise ValueError("Connection capacity must be finite and positive")
        new_id = min(-1, int(network.way_id.min()) - 1)
        geometries = dict(network.geometries or {})
        geometries[new_id] = geometry["coordinates"]
        return replace(
            network,
            geometries=geometries,
            source=np.r_[network.source, a, b],
            target=np.r_[network.target, b, a],
            free_hours=np.r_[network.free_hours, length / speed, length / speed],
            capacity=np.r_[network.capacity, capacity, capacity],
            length_km=np.r_[network.length_km, length, length],
            way_id=np.r_[
                network.way_id,
                min(-1, int(network.way_id.min()) - 1),
                min(-1, int(network.way_id.min()) - 1),
            ],
            shared=np.r_[network.shared, -1, -1],
        )
    ways = project.get("way_ids", [])
    if not ways or any(isinstance(w, bool) or not isinstance(w, int) for w in ways):
        raise ValueError("Project needs integer way_ids")
    selected = np.isin(network.way_id, ways)
    if set(ways) != set(network.way_id[selected].tolist()):
        raise ValueError("Project contains absent road identifiers")
    if kind == "closure":
        keep = ~selected
        if not keep.any():
            raise ValueError("Closure cannot remove every network edge")
        return replace(
            network,
            **{
                key: getattr(network, key)[keep]
                for key in (
                    "source",
                    "target",
                    "free_hours",
                    "capacity",
                    "length_km",
                    "way_id",
                    "shared",
                )
            },
        )
    pairs = np.column_stack(
        (
            network.way_id[selected],
            np.minimum(network.source[selected], network.target[selected]),
            np.maximum(network.source[selected], network.target[selected]),
        )
    )
    _, unique = np.unique(pairs, axis=0, return_index=True)
    length = float(network.length_km[selected][unique].sum())
    nodes = np.unique(np.r_[network.source[selected], network.target[selected]])
    graph = csr_matrix(
        (
            np.ones(selected.sum()),
            (
                np.searchsorted(nodes, network.source[selected]),
                np.searchsorted(nodes, network.target[selected]),
            ),
        ),
        shape=(len(nodes), len(nodes)),
    )
    if connected_components(graph, directed=False, return_labels=False) != 1:
        raise ValueError("An improvement project must cover a contiguous corridor")
    if kind == "capacity":
        lanes = project.get("extra_lanes", 1)
        if (
            isinstance(lanes, bool)
            or not isinstance(lanes, int)
            or not 1 <= lanes <= 5
            or np.any(network.shared[selected] >= 0)
        ):
            raise ValueError(
                "Capacity project requires 1 to 5 extra lanes and no shared lane"
            )
        capacity = network.capacity.copy()
        capacity[selected] += 1800 * lanes
        return replace(network, capacity=capacity)
    raise ValueError(
        "Project kind must be capacity, connection, opening, closure or package"
    )


def connection_design(
    route: dict, surface: RasterGeography, deadline=None, check=None
) -> dict:
    alignment = prepare_alignment(route, surface, deadline, check)
    return {
        **alignment,
        "road_class": "two_lane_connector",
        "lanes_per_direction": 1,
        "surface": "asphalt",
        "capacity_vph": 1800,
        "design_basis": "proposed_screening_parameters_not_surveyed_road_design",
        "speed_basis": {
            "method": "segment_travel_time_harmonic_equivalent",
            "class_design_speed_kmh": 60,
            "review": "provisional_segment_parameters_require_engineered_alignment",
        },
    }
