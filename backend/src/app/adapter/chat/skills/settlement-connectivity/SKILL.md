---
name: settlement-connectivity
description: Compare existing routes between named settlements and the effect of specified closures. Development uses traffic-development.
---

# Existing settlement routes

For existing routes between 2–12 settlements use `calculate_scenario(kind=connectivity)`.
Resolve ambiguous names with atlas queries. `mode=all_pairs` compares pairs; `mode=to_center`
uses the supplied center. `selection_ids` applies jointly resolved closures to the comparison.
Use returned route geometry, travel times, distances and access results. Do not invent connections
or treat a lookup failure as proof that settlements have no road between them.

This route comparison does not assign new traffic or predict queues. For increasing connectivity,
faster transit or congestion relief, load traffic-development and use the requested objective.
Do not attach assumed utilization or queue parameters to this tool.

Read a saved result with `manage_calculation(kind=status, calculation_type=connectivity,
calculation_id=...)`. Use its unchanged saved assumptions when explaining it. Show one map and
summarize the most consequential differences; avoid duplicating the rendered comparison.
