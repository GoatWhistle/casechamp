import math
from itertools import pairwise

import numpy as np
from synthetic_traffic.alignment_validation import (
    AlignmentRejected,
    checkpoint,
    segment_details,
    structure_cells,
)
from synthetic_traffic.geography import polyline_km


def _simplify(points, surface, structures, deadline, check):
    kept = {0, len(points) - 1}
    stack = [(0, len(points) - 1)]
    protected = {
        i for i, point in enumerate(points) if surface.cell(*point) in structures
    }
    while stack:
        checkpoint(deadline, check)
        a, b = stack.pop()
        if b == a + 1:
            failure = {}
            if (
                segment_details(surface, points[a], points[b], structures, failure)
                is None
            ):
                raise AlignmentRejected("raw_edge", failure)
            continue
        anchors = [i for i in protected if a < i < b]
        if not anchors and segment_details(surface, points[a], points[b]) is not None:
            continue
        if anchors:
            split = sorted(anchors)[len(anchors) // 2]
        else:
            delta = points[b] - points[a]
            length = float(delta @ delta)
            offsets = points[a + 1 : b] - points[a]
            distances = (
                np.linalg.norm(
                    offsets - np.outer(np.clip(offsets @ delta / length, 0, 1), delta),
                    axis=1,
                )
                if length
                else np.linalg.norm(offsets, axis=1)
            )
            split = (
                a + 1 + int(np.argmax(distances))
                if distances.max(initial=0) > 1e-12
                else (a + b) // 2
            )
        kept.add(split)
        stack.extend([(a, split), (split, b)])
    return points[sorted(kept)]


def _curve(a, b, c, scale, surface, structures, deadline, check):
    u, v = (b - a) * scale, (c - b) * scale
    before, after = np.linalg.norm(u), np.linalg.norm(v)
    if min(before, after) <= 1e-6:
        return None
    u, v = u / before, v / after
    angle = math.acos(float(np.clip(u @ v, -1, 1)))
    if angle < 1e-5:
        return [b], None
    if angle > math.radians(165):
        return None
    sign = 1 if u[0] * v[1] - u[1] * v[0] > 0 else -1
    last_failure = {}
    for fraction in (0.45, 0.225, 0.1125, 0.05625):
        checkpoint(deadline, check)
        tangent = min(before, after) * fraction
        radius = tangent / math.tan(angle / 2)
        start, finish = b - u * tangent / scale, b + v * tangent / scale
        center = start * scale + np.array([-u[1], u[0]]) * radius * sign
        initial = math.atan2((start * scale - center)[1], (start * scale - center)[0])
        angles = np.linspace(
            initial,
            initial + sign * angle,
            max(
                4,
                math.ceil(radius * angle / (surface.cell_degrees * scale.min() / 4))
                + 1,
            ),
        )
        arc = [
            (center + radius * np.array([math.cos(value), math.sin(value)])) / scale
            for value in angles
        ]
        arc[0], arc[-1] = start, finish
        valid = True
        for p, q in pairwise(arc):
            checkpoint(deadline, check)
            failure = {}
            if segment_details(surface, p, q, structures, failure) is None:
                last_failure = failure
                valid = False
                break
        if valid:
            return arc, radius
    raise AlignmentRejected("fillet", last_failure)


def prepare_alignment(route, surface, deadline=None, check=None):
    points = np.asarray(route["geometry"]["coordinates"], dtype=float)
    if points.ndim != 2 or len(points) < 2 or not np.isfinite(points).all():
        raise ValueError("Alignment requires finite routed coordinates")
    structures = structure_cells(surface, route)
    simplified = _simplify(points, surface, structures, deadline, check)
    if simplified is None:
        raise ValueError("Routed alignment fails full-cell geographic screening")
    scale = np.array([111195.08 * np.cos(np.radians(points[:, 1].mean())), 111195.08])
    chunks = []
    current = simplified[0]
    for i in range(1, len(simplified) - 1):
        checkpoint(deadline, check)
        curve = _curve(
            simplified[i - 1],
            simplified[i],
            simplified[i + 1],
            scale,
            surface,
            structures,
            deadline,
            check,
        )
        if curve is None:
            raise AlignmentRejected(
                "fillet",
                {"reason": "bend_geometry", "cells": [surface.cell(*simplified[i])]},
            )
        arc, radius = curve
        chunks.append((current, arc[0], None))
        chunks.extend((a, b, radius) for a, b in pairwise(arc))
        current = arc[-1]
    chunks.append((current, simplified[-1], None))
    coordinates = [points[0].tolist()]
    segments = []
    for a, b, radius in chunks:
        checkpoint(deadline, check)
        length = polyline_km([a.tolist(), b.tolist()])
        if length < 1e-9:
            continue
        count = max(
            1, math.ceil(length * 1000 / (surface.cell_degrees * scale.min() / 2))
        )
        samples = np.linspace(a, b, count + 1)
        for start, finish in pairwise(samples):
            checkpoint(deadline, check)
            failure = {}
            detail = segment_details(surface, start, finish, structures, failure)
            if detail is None:
                raise AlignmentRejected("smoothed_segment", failure)
            distance = polyline_km([start.tolist(), finish.tolist()])
            curvature = math.sqrt(127 * radius * (0.04 + 0.15)) if radius else 60.0
            grade_cap = 40.0 if detail["maximum_terrain_grade"] > 0.04 else 60.0
            speed = min(60.0, curvature, 40.0 if detail["structure"] else grade_cap)
            segments.append(
                {
                    "from": len(coordinates) - 1,
                    "to": len(coordinates),
                    "length_km": distance,
                    "speed_kmh": speed,
                    "free_hours": distance / speed,
                    "curve_radius_m": radius,
                    **detail,
                }
            )
            coordinates.append(finish.tolist())
    length = sum(item["length_km"] for item in segments)
    hours = sum(item["free_hours"] for item in segments)
    if hours <= 0:
        raise ValueError("Alignment has no positive travel time")
    return {
        "geometry": {"type": "LineString", "coordinates": coordinates},
        "length_km": length,
        "speed_kmh": length / hours,
        "free_travel_hours": hours,
        "travel_segments": segments,
        "alignment_screening": {
            "method": "full_supercover_LOS_post_smoothing_and_validated_circular_fillets",
            "input_vertices": len(points),
            "simplified_vertices": len(simplified),
            "engineered_curve_radii_confirmed": False,
            "superelevation_assumption": 0.04,
            "side_friction_assumption": 0.15,
            "curve_formula": "V_kmh=sqrt(127*R_m*(e+f))",
            "review": "proposed_geometry_requires_survey_sight_distance_vertical_alignment_and_structural_design",
        },
    }


def route_with_retries(
    surface, start, finish, deadline, penalty, remaining, find, design, check=None
):
    rejected = []
    used = 0
    for attempt in range(min(3, remaining)):
        used = attempt + 1
        checkpoint(deadline, check)
        route = find(surface, start, finish, deadline, penalty)
        if route is None:
            return None, None, attempt + 1, rejected
        try:
            prepared = design(route, surface, deadline, check)
            for point in route["geometry"]["coordinates"][1:-1]:
                cell = surface.cell(*point)
                penalty[cell] = penalty.get(cell, 0) + 3
            return route, prepared, attempt + 1, rejected
        except AlignmentRejected as error:
            rejected.append(
                {
                    "reason": error.reason,
                    "stage": error.stage,
                    "cells": [list(cell) for cell in error.cells],
                }
            )
            for row, col in error.cells:
                for dr in (-1, 0, 1):
                    for dc in (-1, 0, 1):
                        cell = row + dr, col + dc
                        if (
                            0 <= cell[0] < surface.blocked.shape[0]
                            and 0 <= cell[1] < surface.blocked.shape[1]
                        ):
                            penalty[cell] = penalty.get(cell, 0) + 12
            if not error.cells:
                break
        except ValueError:
            rejected.append(
                {"reason": "invalid_alignment", "stage": "design", "cells": []}
            )
            break
    return None, None, used, rejected
