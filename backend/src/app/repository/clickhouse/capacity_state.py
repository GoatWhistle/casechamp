from typing import Any


def restore_capacity_defaults(row: dict[str, Any]) -> dict[str, Any]:
    for result in row.get("result") or []:
        if not result.get("road_cost_method"):
            result["road_cost_method"] = "legacy_speed_v1"
    for appraisal in row.get("appraisal_result") or []:
        if not appraisal.get("freight_routing_scope"):
            appraisal["freight_routing_scope"] = "manual_supplied_travel"
    return row
