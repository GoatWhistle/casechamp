from math import isfinite
from typing import Any

from app.domain.appraisal import AppraisalReport, appraise
from app.domain.appraisal_inputs import FreightTravelChange, ProjectAssumptions, TravelChange
from app.domain.errors import InvalidQuery


class AppraisalRouting:
    def __init__(self, project: ProjectAssumptions) -> None:
        self.project = project
        self.freight_before: dict[str, tuple[float, float] | None] = {}
        self.freight_after: dict[str, tuple[float, float] | None] = {}
        self.before_values: dict[tuple[str, str], float | None] = {}
        self.after_values: dict[tuple[str, str], float | None] = {}

    def capture(
        self, ids: list[str], markets: list[str], times: Any
    ) -> dict[tuple[str, str], float | None]:
        origins = {name: i for i, name in enumerate(ids)}
        targets = {name: j for j, name in enumerate(markets)}
        result = {}
        for flow in self.project.passengers:
            if flow.origin_point_id not in origins or flow.market_city not in targets:
                raise InvalidQuery(
                    "Economic origin must belong to the region and target to a market"
                )
            value = float(times[origins[flow.origin_point_id], targets[flow.market_city]])
            result[(flow.origin_point_id, flow.market_city)] = value if isfinite(value) else None
        return result

    def before(self, ids: list[str], markets: list[str], times: Any) -> None:
        self.before_values = self.capture(ids, markets, times)

    def after(self, ids: list[str], markets: list[str], times: Any) -> None:
        self.after_values = self.capture(ids, markets, times)

    def result(self) -> AppraisalReport:
        return appraise(
            self.project,
            [
                TravelChange(
                    p.origin_point_id,
                    p.market_city,
                    self.before_values.get((p.origin_point_id, p.market_city)),
                    self.after_values.get((p.origin_point_id, p.market_city)),
                )
                for p in self.project.passengers
            ],
            self.freight_evidence(),
        )

    def freight_evidence(self) -> list[FreightTravelChange]:
        result = []
        for flow in self.project.freight:
            if not flow.origin_point_id:
                continue
            before = self.freight_before.get(flow.name)
            after = self.freight_after.get(flow.name)
            result.append(
                FreightTravelChange(
                    flow.name,
                    before[0] if before else None,
                    after[0] if after else None,
                    before[1] if before else None,
                    after[1] if after else None,
                )
            )
        return result
