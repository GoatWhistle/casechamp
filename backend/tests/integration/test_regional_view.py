import json
from dataclasses import asdict, replace
from urllib.request import Request, urlopen
from uuid import uuid4

import pytest
from tests.storage import settings
from tests.unit.domain.normative.fire_evidence.factories import facility

from app.domain.errors import DataUnavailable
from app.domain.normative.comparison import compare_routes
from app.domain.normative.model import AccessRow
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.regional_measurements import ClickHouseRegionalMeasurementRepository
from app.repository.clickhouse.regional_view import ClickHouseRegionalViewRepository
from app.usecase.normative.regional_measurements import RegionalMeasurement
from app.usecase.normative.regional_view import RegionalMapBounds


def test_complete_regional_data_is_available_through_pages_points_and_conserved_map_cells() -> None:
    config = settings()
    reader = ClickHouseReader(
        config.clickhouse_url, config.clickhouse_user, config.clickhouse_password, max_threads=1
    )
    table = "plexus_normative.test_regional_view_" + uuid4().hex

    def command(sql: str) -> None:
        with urlopen(
            Request(reader.url + "/", data=sql.encode(), headers=reader.headers), timeout=60
        ) as response:
            response.read()

    for suffix in ("", "_rows", "_facilities"):
        command(f"CREATE TABLE {table}{suffix} AS plexus_normative.regional_measurements{suffix}")
    try:
        store = ClickHouseRegionalMeasurementRepository(reader)
        store.table = table
        target = replace(facility(), latitude=55, longitude=65)
        rows = [
            AccessRow(
                f"p{250 - i:03}",
                f"Place {i:03}",
                None,
                55 + i / 1000,
                65 + i / 1000,
                target.id,
                None,
                None,
                "unknown",
                distance_metres=None if i % 5 == 0 else float(i),
                routing_node=1,
                approach_metres=1.23456789,
            )
            for i in range(251)
        ]
        rows.extend(
            [
                replace(rows[1], id="east", longitude=179.5),
                replace(rows[0], id="west", longitude=-179.5),
            ]
        )
        result = RegionalMeasurement(
            uuid4().hex,
            "R",
            "Region",
            "N04",
            "school",
            "graph",
            "2026-11-12T12:00:00Z",
            [target],
            rows,
            rows,
            [],
            compare_routes(rows, rows, "metres"),
            model_revision="regional-walk-v1",
            mode="walk",
            unit="metres",
        )
        store.save(result)
        repository = ClickHouseRegionalViewRepository(reader, table)
        view = repository.latest_view("R", "N04")
        assert view is not None and view.origins == len(rows)
        first = repository.rows(view, "scenario", 1, 50, "position", False, "")
        second = repository.rows(view, "scenario", 2, 50, "position", False, "")
        assert first.rows == rows[:50]
        assert second.rows == rows[50:100]
        assert not {r.id for r in first.rows} & {r.id for r in second.rows}
        assert first.total == len(rows)
        expensive = repository.rows(view, "scenario", 1, 10, "cost", True, "")
        assert [r.distance_metres for r in expensive.rows] == sorted(
            [r.distance_metres for r in rows if r.distance_metres is not None], reverse=True
        )[:10]
        found = repository.rows(view, "scenario", 1, 50, "position", False, "PLACE 001")
        assert [r.id for r in found.rows] == [rows[1].id, "east"]
        world = repository.map_view(view, "scenario", RegionalMapBounds(-180, -90, 180, 90), 20)
        assert len(world.cells) <= 4096
        assert sum(c.references for c in world.cells) == len(rows)
        assert sum(c.measured for c in world.cells) == sum(
            r.distance_metres is not None for r in rows
        )
        assert sum(c.facilities for c in world.facilities) == 1
        crossing = repository.map_view(view, "scenario", RegionalMapBounds(170, -90, -170, 90), 5)
        assert crossing.viewport_references == 2
        assert sorted(c.origin_id for c in crossing.cells if c.origin_id) == ["east", "west"]
        assert next(c for c in crossing.cells if c.origin_id == "west").minimum is None
        detail = repository.point(view, "scenario", "east")
        assert detail is not None and detail.row == rows[-2] and detail.facility == target
        assert repository.facilities(view, 1, 10, "").facilities == [target]
        legacy = replace(result, run_id=uuid4().hex, region_id="Legacy")
        command(
            f"INSERT INTO {table} FORMAT JSONEachRow\n"
            + json.dumps(
                {
                    "id": legacy.run_id,
                    "region_id": legacy.region_id,
                    "criterion_id": legacy.criterion_id,
                    "saved_at": legacy.saved_at,
                    "payload": json.dumps(asdict(legacy)),
                }
            )
        )
        old = repository.view(legacy.run_id)
        assert old is not None
        assert repository.rows(old, "scenario", 2, 50, "position", False, "").rows == second.rows
        old_map = repository.map_view(old, "scenario", RegionalMapBounds(170, -90, -170, 90), 5)
        assert old_map.viewport_references == 2
        command(
            f"ALTER TABLE {table}_rows DELETE WHERE run_id='{result.run_id}' AND stage='scenario' AND position=250 SETTINGS mutations_sync=1"
        )
        with pytest.raises(DataUnavailable):
            ClickHouseRegionalViewRepository(reader, table).view(result.run_id)
    finally:
        for suffix in ("", "_rows", "_facilities"):
            command(f"DROP TABLE {table}{suffix}")
