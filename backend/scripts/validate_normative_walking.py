import hashlib
import json
import os
from dataclasses import asdict
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from app.adapter.normative.walking_routing import WalkingNormativeRouting
from app.domain.normative.walking import metres_between
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.normative import ClickHouseNormativeRepository
from app.repository.clickhouse.pedestrian import ClickHousePedestrianRepository
from app.settings import load_settings


def main() -> None:
    config = load_settings(os.environ)
    reader = ClickHouseReader(
        config.clickhouse_url, config.clickhouse_user, config.clickhouse_password
    )
    repository = ClickHouseNormativeRepository(reader)
    routing = WalkingNormativeRouting(ClickHousePedestrianRepository(reader, "37000000", "pilot"))
    origins = repository.walking_origins(routing.revision)
    sample = sorted(
        origins,
        key=lambda row: hashlib.sha256(("walking-control-v1:" + row.id).encode()).hexdigest(),
    )[:64]
    facilities = repository.facilities("school")
    before = routing.evaluate(sample, facilities, 500, [])
    graph = routing.prepare()
    assert np.all(np.isfinite(graph.edges[:, 2])) and np.all(graph.edges[:, 2] > 0)
    assert np.min(graph.edges[:, :2]) >= 0
    assert np.max(graph.edges[:, :2]) < len(graph.coordinates)
    by_facility = {row.id: row for row in facilities}
    for origin, row in zip(sample, before, strict=True):
        assert row.population is None and row.minutes is None and row.state == "unknown"
        if row.distance_metres is None:
            continue
        assert row.facility_id is not None
        facility = by_facility[row.facility_id]
        assert origin.latitude is not None and origin.longitude is not None
        assert facility.latitude is not None and facility.longitude is not None
        straight = metres_between(
            (origin.longitude, origin.latitude), (facility.longitude, facility.latitude)
        )
        assert row.distance_metres + 1 >= straight
    ways: set[int] = set()
    for origin in sample[:8]:
        attached = graph.attach(origin.latitude, origin.longitude)
        if attached is not None:
            ways.update(int(value) for value in graph.edges[graph.edges[:, 0] == attached.left, 3])
    closed = sorted(ways)[:20]
    after = routing.evaluate(sample, facilities, 500, closed)
    increased, lost, unchanged = 0, 0, 0
    for first, second in zip(before, after, strict=True):
        if first.distance_metres is None:
            assert second.distance_metres is None
        elif second.distance_metres is None:
            lost += 1
        else:
            assert second.distance_metres + 1e-6 >= first.distance_metres
            if second.distance_metres > first.distance_metres + 1e-6:
                increased += 1
            else:
                unchanged += 1
    report = {
        "method": "walking-control-v1",
        "measured_at": datetime.now(UTC).isoformat(),
        "graph_revision": routing.revision,
        "rules_version": "pedestrian-v2",
        "origins_total": len(origins),
        "sample_size": len(sample),
        "node_count": len(graph.coordinates),
        "edge_count": len(graph.edges),
        "baseline_paths": sum(row.distance_metres is not None for row in before),
        "closed_way_ids": closed,
        "distance_increased": increased,
        "paths_lost": lost,
        "unchanged_paths": unchanged,
        "limits": [
            "Reference coordinates are not verified entrances",
            "Population, legal applicability and service operation remain unknown",
        ],
        "baseline_rows": [asdict(row) for row in before],
        "scenario_rows": [asdict(row) for row in after],
    }
    path = Path("../docs/results/normative-walking-validation.json")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")
    print(
        json.dumps(
            {
                key: value
                for key, value in report.items()
                if key not in ("baseline_rows", "scenario_rows")
            }
        )
    )


if __name__ == "__main__":
    main()
