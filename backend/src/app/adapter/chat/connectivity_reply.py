import json
from copy import deepcopy
from typing import Any

WAY_LISTS = {
    "closed_way_ids": "closed_way_count",
    "source_way_ids": "source_way_count",
    "assumed_source_lane_ways": "assumed_source_lane_way_count",
    "way_ids": "way_count",
    "assumed_lane_ways": "assumed_lane_way_count",
}


def connectivity_reply(result: dict[str, Any]) -> str:
    summary = deepcopy(result)
    summary["detail"] = "summary"
    summarize_ways(summary)
    for pair in summary["pairs"]:
        traffic = pair.get("traffic")
        if traffic is None:
            continue
        summarize_ways(traffic)
        traffic.pop("assumptions", None)
        for assigned in traffic["routes"]:
            route = assigned["route"]
            summarize_ways(route)
            route.pop("segments", None)
    return json.dumps(summary, ensure_ascii=False, allow_nan=False)


def summarize_ways(row: dict[str, Any]) -> None:
    for key, count_key in WAY_LISTS.items():
        if key in row:
            row[count_key] = len(row.pop(key))
