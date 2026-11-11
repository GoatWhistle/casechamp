from typing import Any

from app.domain.appraisal import AppraisalReport, AppraisalScenario
from app.domain.appraisal_inputs import (
    DemandScenario,
    FreightFlow,
    FreightTravelChange,
    PassengerFlow,
    ProjectAssumptions,
    TravelChange,
)


def restore_appraisal(row: dict[str, Any]) -> None:
    project = row.get("appraisal_assumptions")
    if project:
        row["appraisal_assumptions"] = ProjectAssumptions(
            **{
                **project,
                "passengers": [PassengerFlow(**p) for p in project["passengers"]],
                "freight": [FreightFlow(**f) for f in project.get("freight", [])],
                "scenarios": [DemandScenario(**s) for s in project["scenarios"]],
            }
        )
    report = row.get("appraisal_result")
    if report:
        report["freight_routing_scope"] = (
            report.get("freight_routing_scope") or "manual_supplied_travel"
        )
        row["appraisal_result"] = AppraisalReport(
            **{
                **report,
                "travel": [TravelChange(**r) for r in report["travel"]],
                "freight_travel": [
                    FreightTravelChange(**r) for r in report.get("freight_travel", [])
                ],
                "scenarios": [AppraisalScenario(**s) for s in report["scenarios"]],
            }
        )
