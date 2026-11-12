import math

import numpy as np
from shapely import prepare
from shapely.geometry import LineString, MultiLineString, box
from synthetic_traffic.geography import RasterGeography
from synthetic_traffic.model import Network


def screen_capacity(network: Network, project: dict, surface: RasterGeography | None):
    if surface is None:
        return None
    ways = project.get("way_ids", [])
    selected = np.flatnonzero(np.isin(network.way_id, ways))
    if not len(selected) or not ways:
        return None
    if any(
        item.get("kind") in {"bridge", "tunnel"}
        for item in project.get("structures", [])
    ):
        return None
    lanes = project.get("extra_lanes", 1)
    if isinstance(lanes, bool) or not isinstance(lanes, int) or not 1 <= lanes <= 5:
        return None
    segments = []
    seen = set()
    geometries = getattr(network, "geometries", None) or {}
    for way in ways:
        geometry = geometries.get(way) or geometries.get(str(way))
        if geometry:
            if isinstance(geometry, list):
                geometry = {"type": "LineString", "coordinates": geometry}
            lines = (
                [geometry["coordinates"]]
                if geometry.get("type") == "LineString"
                else geometry.get("coordinates", [])
            )
            segments.extend(LineString(line) for line in lines)
            continue
        for edge in selected[network.way_id[selected] == way]:
            a, b = int(network.source[edge]), int(network.target[edge])
            key = min(a, b), max(a, b)
            if key in seen:
                continue
            seen.add(key)
            segments.append(
                LineString(
                    [(network.lon[a], network.lat[a]), (network.lon[b], network.lat[b])]
                )
            )
    if not segments:
        return None
    geometry = MultiLineString(segments)
    latitude = surface.origin_lat + surface.cell_degrees * surface.blocked.shape[0] / 2
    meters_degree = 111000 * min(1.0, math.cos(math.radians(latitude)))
    if meters_degree <= 0:
        return None
    existing_lanes_direction = max(1.0, float(network.capacity[selected].max()) / 1800)
    width_m = 3.5 * (existing_lanes_direction + lanes)
    footprint = geometry.buffer(width_m / meters_degree)
    prepare(footprint)
    west, south, east, north = footprint.bounds
    if (
        west < surface.origin_lon
        or south < surface.origin_lat
        or east
        > surface.origin_lon + (surface.blocked.shape[1] - 1) * surface.cell_degrees
        or north
        > surface.origin_lat + (surface.blocked.shape[0] - 1) * surface.cell_degrees
    ):
        return None
    start, finish = surface.cell(west, south), surface.cell(east, north)
    if start is None or finish is None:
        return None
    half = surface.cell_degrees / 2
    elevations = {}
    for row in range(
        max(0, start[0] - 1), min(surface.blocked.shape[0], finish[0] + 2)
    ):
        for col in range(
            max(0, start[1] - 1), min(surface.blocked.shape[1], finish[1] + 2)
        ):
            lon, lat = surface.coordinate((row, col))
            if not footprint.intersects(
                box(lon - half, lat - half, lon + half, lat + half)
            ):
                continue
            if surface.blocked[row, col] or surface.water[row, col]:
                return None
            elevations[row, col] = float(surface.elevation_m[row, col])
    if not elevations:
        return None
    for (row, col), elevation in elevations.items():
        for dr, dc in ((1, 0), (0, 1), (1, 1), (1, -1)):
            other = elevations.get((row + dr, col + dc))
            if other is None:
                continue
            distance_m = (
                surface.cell_degrees
                * 111000
                * math.hypot(dr, dc * math.cos(math.radians(latitude)))
            )
            if abs(other - elevation) / distance_m > surface.max_grade:
                return None
    return {
        "housing_clearance": True,
        "geography_clearance": True,
        "widening_buffer_m": width_m,
        "clearance_basis": "sourced_existing_graph_segments_with_conservative_raster_footprint",
        "geography_sources": surface.sources,
        "structural_inventory": "original_bridge_and_tunnel_tags_unavailable",
        "structure_checks": "raster_water_grade_and_explicit_project_structures_only",
        "review": "raster_screened_widening_requires_structural_and_right_of_way_survey",
    }
