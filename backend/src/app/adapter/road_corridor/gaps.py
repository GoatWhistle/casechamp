from typing import Any

import numpy as np


def gap_pairs(
    ids: Any, xy: Any, labels: Any, pairs: list[tuple[int, int]], max_km: float
) -> list[tuple[int, int]]:
    if not len(xy):
        return []
    scale = float(np.cos(np.radians(np.mean(xy[:, 1]))))
    km = np.column_stack([xy[:, 0] * scale, xy[:, 1]]) * 111.195
    result = []
    components = np.unique(labels)
    for position, component in enumerate(components):
        inside = np.flatnonzero(labels == component)
        outside = np.flatnonzero(labels > component)
        if not len(outside):
            continue
        best: dict[int, tuple[float, int, int]] = {}
        for start in range(0, len(inside), 256):
            chunk = inside[start : start + 256]
            distance = np.hypot(
                km[chunk, None, 0] - km[None, outside, 0], km[chunk, None, 1] - km[None, outside, 1]
            )
            for row, column in zip(*np.nonzero(distance <= max_km), strict=True):
                other = int(labels[outside[column]])
                value = float(distance[row, column])
                if other not in best or value < best[other][0]:
                    best[other] = (value, int(chunk[row]), int(outside[column]))
        result += [(int(ids[a]), int(ids[b])) for _, a, b in best.values()]
    return result
