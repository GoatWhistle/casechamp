import heapq
import itertools
import math
import time

from synthetic_traffic.geography import RasterGeography, polyline_km


def find_corridor(surface: RasterGeography, start, finish, deadline=None, penalty=None):
    source, target = surface.cell(*start), surface.cell(*finish)
    if (
        source is None
        or target is None
        or surface.blocked[source]
        or surface.blocked[target]
    ):
        return None
    offsets = ((0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (-1, -1), (1, -1), (-1, 1))
    radians = math.pi / 180
    delta = surface.cell_degrees * radians
    rows, cols = surface.blocked.shape
    row_lat = [
        (surface.origin_lat + row * surface.cell_degrees) * radians
        for row in range(rows)
    ]
    lengths = {}
    for row in range(rows):
        for dr, dc in offsets:
            if 0 <= row + dr < rows:
                hav = (
                    math.sin(dr * delta / 2) ** 2
                    + math.cos(row_lat[row])
                    * math.cos(row_lat[row + dr])
                    * math.sin(dc * delta / 2) ** 2
                )
                lengths[row, dr, dc] = 12742.0176 * math.asin(math.sqrt(min(1.0, hav)))
    target_lat = row_lat[target[0]]

    def heuristic(cell):
        hav = (
            math.sin((row_lat[cell[0]] - target_lat) / 2) ** 2
            + math.cos(row_lat[cell[0]])
            * math.cos(target_lat)
            * math.sin((cell[1] - target[1]) * delta / 2) ** 2
        )
        return 12742.0176 * math.asin(math.sqrt(min(1.0, hav)))

    queue = [(heuristic(source), 0.0, source)]
    costs = {source: 0.0}
    previous = {}
    modes = {}
    while queue:
        if deadline is not None and time.monotonic() >= deadline:
            return None
        _, queued_cost, current = heapq.heappop(queue)
        if queued_cost != costs[current]:
            continue
        if current == target:
            cells = [current]
            while current != source:
                current = previous[current]
                cells.append(current)
            cells.reverse()
            coordinates = (
                [list(start)]
                + [surface.coordinate(cell) for cell in cells]
                + [list(finish)]
            )
            coordinates = [
                point
                for i, point in enumerate(coordinates)
                if i == 0 or point != coordinates[i - 1]
            ]
            structures = []
            recorded = set()
            for a, b in itertools.pairwise(cells):
                mode = modes[b]
                if mode == "road":
                    continue
                footprint = {a, b}
                if a[0] != b[0] and a[1] != b[1]:
                    footprint.update({(a[0], b[1]), (b[0], a[1])})
                for cell in footprint:
                    if mode == "bridge" and not surface.water[cell]:
                        continue
                    if (mode, cell) not in recorded:
                        structures.append(
                            {"kind": mode, "coordinate": surface.coordinate(cell)}
                        )
                        recorded.add((mode, cell))
            for kind, maximum in (
                ("bridge", surface.max_bridge_km),
                ("tunnel", surface.max_tunnel_km),
            ):
                run = 0.0
                for a, b in itertools.pairwise(cells):
                    run = (
                        run
                        + polyline_km([surface.coordinate(a), surface.coordinate(b)])
                        if modes[b] == kind
                        else 0.0
                    )
                    if run > maximum:
                        return None
            return {
                "geometry": {"type": "LineString", "coordinates": coordinates},
                "length_km": polyline_km(coordinates),
                "structures": structures,
                "geography_sources": surface.sources,
                "review": "raster_screened_requires_engineering_survey",
            }
        for dr, dc in offsets:
            neighbor = current[0] + dr, current[1] + dc
            if (
                not (0 <= neighbor[0] < rows and 0 <= neighbor[1] < cols)
                or surface.blocked[neighbor]
            ):
                continue
            if (
                dr
                and dc
                and (
                    surface.blocked[current[0], neighbor[1]]
                    or surface.blocked[neighbor[0], current[1]]
                )
            ):
                continue
            if (
                dr
                and dc
                and not surface.water[current]
                and not surface.water[neighbor]
                and (
                    surface.water[current[0], neighbor[1]]
                    or surface.water[neighbor[0], current[1]]
                )
            ):
                continue
            length = lengths[current[0], dr, dc]
            grade = abs(
                surface.elevation_m[neighbor] - surface.elevation_m[current]
            ) / (length * 1000)
            if dr and dc:
                start_height = float(surface.elevation_m[current])
                end_height = float(surface.elevation_m[neighbor])
                side_heights = float(
                    surface.elevation_m[current[0], neighbor[1]]
                ) + float(surface.elevation_m[neighbor[0], current[1]])
                grade = max(
                    abs(side_heights - 2 * start_height),
                    abs(2 * end_height - side_heights),
                ) / (length * 1000)
            mode = (
                "bridge"
                if surface.water[current] or surface.water[neighbor]
                else "tunnel"
                if grade > surface.max_grade
                else "road"
            )
            weight = {"road": 1, "bridge": 4, "tunnel": 8}[mode]
            cost = costs[current] + length * weight * (
                1 + (penalty or {}).get(neighbor, 0)
            )
            if cost >= costs.get(neighbor, float("inf")):
                continue
            costs[neighbor], previous[neighbor], modes[neighbor] = cost, current, mode
            heapq.heappush(queue, (cost + heuristic(neighbor), cost, neighbor))
    return None
