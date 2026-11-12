---
name: road-scenarios
description: Assess a concrete road or bridge closure and inspect its verified consequences. For improvements use traffic-development.
---

# Road closure consequences

Use this workflow only for the impact of a specified closure or the criticality of existing roads.
For improving connectivity, transit or congestion, load traffic-development and use its single search.
Do not construct a road, change road speeds, assume traffic loads or simulate queues through older tools.

Resolve a road with `find_transport(kind=road, origin=..., destination=..., road_name=...)`.
Omit road_name when the user means the route between places. For a street within one town,
use that qualified town for both endpoints. Use `find_transport(kind=bridges)` for bridges.
Use the returned selection IDs; never manufacture way IDs from a name or enumerate a corridor by hand.

Call `calculate_scenario(kind=close_selection, selection_ids=[...])` for combined regional
index and national road consequences. Submit all simultaneous closures together. `parent_id`
adds a closure to an existing impact result. `assessment=hansen` requests only the regional index.
`region_ids` extends the requested index coverage. Do not infer total isolation from a failed
attachment or an unresolved route; report the returned calculation error.

For critical roads without a selected closure, use `calculate_scenario(kind=road_analysis,
region_id=..., mode=criticality)`. Historical analysis results remain readable. The previous
improvement mode is unavailable; use traffic-development for new recommendations.

Read saved results with `manage_calculation(kind=status, calculation_id=...)`, use cancel to stop.
For saved national effects use `inspect_road_stress_test`; `compare_stress_route` checks a named
before/after route. Present returned road geometry once. Explain the important affected places,
verified time changes, lost alternatives and remaining routes in a short answer.
