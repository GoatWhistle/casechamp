from collections import defaultdict
from typing import Any

import numpy as np
from scipy.sparse.csgraph import connected_components

from app.domain.road_stress import compare_market_times
from app.usecase.road_stress import StressImpact, StressMarketChange, StressPoint, StressRegion


def disconnected_points(graph: Any, points: list[StressPoint], markets: Any) -> Any:
    _, labels = connected_components(graph, directed=False)
    sources = np.array([c[1] for c in markets], dtype=np.int64)
    counts = np.bincount(labels[sources], minlength=int(labels.max()) + 1)
    own = {str(c[4]) for c in markets}
    return np.array([counts[labels[p.node]] - int(p.id in own) == 0 for p in points])


def point_impact(point: StressPoint, before: Any, after: Any,
                 markets: list[str], own: str) -> StressImpact | None:
    lost, isolated, delay, worst = compare_market_times(before.tolist(), after.tolist(), markets, own)
    if not lost and delay < 1:
        return None
    changes = [StressMarketChange(name, float(a), float(b) if np.isfinite(b) else None)
               for name, a, b in zip(markets, before, after, strict=True)
               if name != own and np.isfinite(a) and (not np.isfinite(b) or (b - a) * 60 >= 1)]
    return StressImpact(point, lost, isolated, delay, worst, changes)


def region_impacts(impacts: list[StressImpact]) -> list[StressRegion]:
    grouped: dict[str, list[StressImpact]] = defaultdict(list)
    for impact in impacts:
        grouped[impact.point.region].append(impact)
    regions = [StressRegion(name, len(rows), sum(r.point.population for r in rows),
                           sum(r.point.population for r in rows if r.external_isolation))
               for name, rows in grouped.items()]
    return sorted(regions, key=lambda r: (-r.isolated_population, -r.population, r.name))
