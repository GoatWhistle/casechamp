from urllib.request import Request, urlopen
from uuid import uuid4

import pytest
from tests.storage import settings

from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.stress import ClickHouseStressStore
from app.usecase.road_stress import StressImpact, StressMarketChange, StressPoint


def test_regional_consequences_compare_same_routes_and_count_residents_once() -> None:
    config = settings()
    reader = ClickHouseReader(
        config.clickhouse_url, config.clickhouse_user, config.clickhouse_password
    )
    store = ClickHouseStressStore(reader)
    key = uuid4().hex

    def impact(
        id: str,
        population: int,
        region: str,
        lost: int,
        isolated: bool,
        delay: float,
        changes: list[StressMarketChange],
    ) -> StressImpact:
        return StressImpact(
            StressPoint(id, id, region, population, 1, 0, 30, 50),
            lost,
            isolated,
            delay,
            changes[0].market,
            changes,
        )

    rows = [
        impact(
            "A",
            100,
            "R",
            1,
            False,
            90,
            [StressMarketChange("City", 1, 2.5), StressMarketChange("Other", 3, None)],
        ),
        impact("B", 50, "R", 1, True, 0, [StressMarketChange("City", 1.5, None)]),
        impact(
            "C",
            200,
            "R",
            0,
            False,
            120,
            [StressMarketChange("Long", 4, 6), StressMarketChange("Nearby", 1, 1.25)],
        ),
        impact("D", 1000, "Elsewhere", 0, False, 240, [StressMarketChange("City", 1, 5)]),
    ]
    try:
        store.save_impacts(key, rows)
        store.save_impacts(key, rows)
        result = store.consequences(key, "R")
        assert result.lost_connections == 2
        assert result.settlements_losing_connections == 2
        assert result.residents_losing_connections == 150
        assert [
            (b.threshold_minutes, b.settlements, b.residents) for b in result.delay_exposure
        ] == [
            (30, 2, 300),
            (60, 2, 300),
            (120, 1, 200),
        ]
        nearby = result.nearby_access
        assert nearby.changed_connections == 3
        assert nearby.lost_connections == 1
        assert nearby.comparable_connections == 2
        assert nearby.mean_before_minutes == pytest.approx(60)
        assert nearby.mean_after_minutes == pytest.approx(112.5)
        assert nearby.mean_added_minutes == pytest.approx(52.5)
        assert nearby.connections_crossing_threshold == 2
        assert nearby.settlements_crossing_threshold == 2
        assert nearby.residents_crossing_threshold == 150
        city = next(d for d in result.destinations if d.destination == "City")
        assert city.exposed_residents == 150
        assert city.residents_losing_connection == 50
        assert city.mean_before_minutes == 60
        assert city.mean_after_minutes == 150
        assert any(e.after_minutes is None and e.added_minutes is None for e in result.examples)
        assert {e.origin_id for e in result.examples} <= {"A", "B", "C"}
        empty = store.consequences(key, "Missing")
        assert empty.lost_connections == 0
        assert empty.nearby_access.mean_after_minutes is None
        assert empty.examples == []
    finally:
        request = Request(
            reader.url,
            data=(
                f"ALTER TABLE plexus_state.stress_point_impacts DELETE WHERE job_id='{key}' SETTINGS mutations_sync=1"
            ).encode(),
            headers=reader.headers,
        )
        with urlopen(request, timeout=30) as response:
            response.read()
