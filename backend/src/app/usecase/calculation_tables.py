import json
import re
from dataclasses import asdict, replace
from typing import Literal

from app.domain.errors import DataUnavailable, InvalidQuery
from app.usecase.chat_artifacts import ChatCell, ChatColumn, ChatTable
from app.usecase.closure_assessment import closure_indices
from app.usecase.road_graph import RoadGraph
from app.usecase.road_stress import StressPort

TableView = Literal["indices", "routes", "access"]


class CalculationTables:
    def __init__(self, roads: RoadGraph | None, stress: StressPort | None) -> None:
        self.roads, self.stress = roads, stress

    def build(
        self,
        scenario_ids: list[str],
        stress_ids: list[str],
        view: TableView = "indices",
        regions: list[str] | None = None,
    ) -> list[ChatTable]:
        if not 1 <= len(scenario_ids) + len(stress_ids) <= 12:
            raise InvalidQuery("Select 1 to 12 saved calculations")
        tables = []
        covered: set[str] = set()
        columns: tuple[ChatColumn, ...]
        for key in dict.fromkeys(stress_ids):
            if self.stress is None:
                raise DataUnavailable("Closure results unavailable")
            job = self.stress.get(key)
            if job.status != "completed":
                raise InvalidQuery("Wait for the closure to complete")
            indices = closure_indices(self.roads, job)
            covered.update(index.id for index in indices)
            names = self.stress.geometry(key).names
            references = [
                name
                for name in names
                if re.fullmatch(r"[А-ЯA-Z]{1,3}[-– ]?\d+[А-ЯA-Zа-яa-z]?", name)
            ]
            caption = ", ".join(references or names[:3])
            selected = (
                regions
                or sorted({index.region for index in indices})
                or [r.name for r in job.regions[:5]]
            )
            if view == "indices":
                rows: list[dict[str, ChatCell]] = []
                for index in indices:
                    if regions and index.region not in regions and index.region_id not in regions:
                        continue
                    if index.status in {"queued", "running"}:
                        raise InvalidQuery("Wait for the regional indices to complete")
                    if index.result is None:
                        continue
                    rows.append(
                        {
                            "id": index.id,
                            "name": index.region,
                            "before": index.result.before,
                            "after": index.result.after,
                            "delta": index.result.delta,
                        }
                    )
                columns = (
                    ChatColumn("name"),
                    ChatColumn("before", "number"),
                    ChatColumn("after", "number"),
                    ChatColumn("delta", "number"),
                )
            else:
                rows = []
                for region in selected:
                    summary = self.stress.summary(key, region)
                    consequence = summary.consequences
                    if consequence is None:
                        continue
                    if view == "access":
                        exposure = next(
                            (e for e in consequence.delay_exposure if e.threshold_minutes == 60),
                            None,
                        )
                        rows.append(
                            {
                                "id": key + ":" + summary.region,
                                "name": summary.region,
                                "lost_nearby": consequence.nearby_access.lost_connections,
                                "delayed_residents": exposure.residents if exposure else None,
                            }
                        )
                    else:
                        for i, example in enumerate(consequence.examples):
                            rows.append(
                                {
                                    "id": key + ":" + summary.region + ":" + str(i),
                                    "origin": example.origin,
                                    "destination": example.destination,
                                    "before_minutes": example.before_minutes,
                                    "after_minutes": example.after_minutes,
                                    "status_after": "unreachable"
                                    if example.after_minutes is None
                                    else "reachable",
                                }
                            )
                columns = (
                    (
                        ChatColumn("name"),
                        ChatColumn("lost_nearby", "integer"),
                        ChatColumn("delayed_residents", "integer"),
                    )
                    if view == "access"
                    else (
                        ChatColumn("origin"),
                        ChatColumn("destination"),
                        ChatColumn("before_minutes", "number"),
                        ChatColumn("after_minutes", "number"),
                    )
                )
            if rows:
                title: Literal["scenario_indices", "scenario_routes", "scenario_access"] = (
                    "scenario_indices"
                    if view == "indices"
                    else "scenario_routes"
                    if view == "routes"
                    else "scenario_access"
                )
                tables.append(
                    ChatTable(
                        "comparison-" + key + "-" + view,
                        title,
                        columns,
                        tuple(rows),
                        len(rows),
                        False,
                        "model:closure:" + key,
                        caption,
                    )
                )
        if scenario_ids and view != "indices":
            raise InvalidQuery("Route and access tables require stress_ids")
        grouped: dict[str, int] = {}
        for key in dict.fromkeys(scenario_ids):
            if key in covered:
                continue
            if self.roads is None:
                raise DataUnavailable("Index results unavailable")
            index_job = self.roads.job(key)
            if index_job.status != "completed" or index_job.result is None:
                raise InvalidQuery("Wait for the regional index to complete")
            result = index_job.result
            signature = json.dumps(
                {
                    "version": index_job.version,
                    "scenario": index_job.scenario,
                    "changes": [
                        asdict(c) for c in sorted(index_job.changes, key=lambda c: c.way_id)
                    ],
                    "links": [asdict(link) for link in index_job.links],
                    "addition": asdict(index_job.addition) if index_job.addition else None,
                },
                sort_keys=True,
            )
            row: dict[str, ChatCell] = {
                "id": key,
                "name": index_job.region,
                "before": result.before,
                "after": result.after,
                "delta": result.delta,
            }
            if signature in grouped:
                position = grouped[signature]
                previous = tables[position]
                tables[position] = replace(
                    previous, rows=(*previous.rows, row), total=previous.total + 1
                )
                continue
            names = (
                self.roads.geometry([change.way_id for change in index_job.changes]).names
                if index_job.changes
                else []
            )
            references = [
                name
                for name in names
                if re.fullmatch(r"[А-ЯA-Z]{1,3}[-– ]?\d+[А-ЯA-Zа-яa-z]?", name)
            ]
            caption = ", ".join(references or names[:3])
            grouped[signature] = len(tables)
            table = ChatTable(
                "comparison-" + key,
                "scenario_indices",
                (
                    ChatColumn("name"),
                    ChatColumn("before", "number"),
                    ChatColumn("after", "number"),
                    ChatColumn("delta", "number"),
                ),
                (
                    {
                        "id": key,
                        "name": index_job.region,
                        "before": result.before,
                        "after": result.after,
                        "delta": result.delta,
                    },
                ),
                1,
                False,
                "model:scenario:" + key,
                caption,
            )
            tables.append(table)
        return [
            replace(table, rows=table.rows[:30], truncated=len(table.rows) > 30) for table in tables
        ]
