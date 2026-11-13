---
name: road-scenarios
description: Diagnose municipal accessibility deficits, inspect road load, compare lane additions or closures, and plan journeys without a car.
---

# Municipal accessibility and road scenarios

For a regional diagnosis, follow Municipal diagnosis. For a specified road or bridge closure
without a municipal load study, follow Regional closure below. For travel without a car,
follow Public transport journey after identifying the origin and facility.
Automatic road-development search has been removed. Use saved load and supported interventions;
new road construction and direct speed changes are unavailable in this workflow.

## Municipal diagnosis

Configure lane additions and closures through the agent tools only; do not direct the user to
scenario buttons or direction selectors. Resolve the requested segment and direction in chat.
If direction is ambiguous, ask before starting. Segment coordinates run from the first endpoint
to the last; reverse_edge_index denotes the opposite direction.

For “find a problematic municipality”, call `municipal_analysis(action=diagnose, region_id=...)`.
It selects the lowest measured city connectivity below the regional value, not a universal
quality-of-life ranking. Report its name, value versus region, relative shortfall and measurement
coverage. If no candidate is confirmed, say so. Mention ties or incomplete coverage when present.
Then call `indices` for that municipality to inspect saved service access, and `baseline` to inspect
road load. Missing load means not yet assessed, never no congestion. Use confirmed service deficits
only; unknown measurements are not lost access. If useful, call `access` for a deficient service
to name affected settlements and measured journey times. Never infer road congestion from low
connectivity alone or claim widening will help before comparing a calculated scenario.
Keep the answer short: municipality, two or three numeric reasons, then one road scenario to test.
Distinguish observed weaknesses from their unverified causes.
When the user asks for a solution and its effect, complete diagnosis -> indices -> improve in
one flow. Do not stop at a shortlist or request a separate calculation confirmation.
Call `municipal_analysis(action=improve, region_id=..., municipality_id=...)` once: it selects
one supported directed segment by saved load and submits one extra lane in that direction only.
State the selected direction from returned endpoint coordinates; this is an analyst-selected
proposal, so no extra direction question is needed. This is one tested hypothesis, not an optimum.
If baseline is unavailable, present the hypothesis as pending; do not invent numerical effects.
If a job was returned, reuse its calculation_id for status; never call improve again to poll.
After completion use comparison for all available before/after indicators: city connectivity
for district and region, road time, overload, unserved trips and six car-service access criteria.
Show zero and negative effects too; distinguish index points, minutes and percentage points.
Service percentages describe reference points, not residents. Walking and transit remain
not recalculated. A weak or harmful result must be called unsuccessful, not recommended as a win.

After selecting a municipality, call `municipal_analysis(action=roads, region_id=...,
municipality_id=..., criterion_id=N01, limit=5)` to find local candidate segments before load is ready.
Without traffic it orders by road class and proximity to saved reference points; never call that order a congestion ranking.
With traffic it ranks by corridor peak load; that peak need not belong to the sampled segment.
The response includes graph coverage, one sample segment per road name and up to three nearby
reference points from a bounded saved sample. Proximity is not proof their routes use that road.
Missing nearby samples does not mean no affected residents. Use returned `directed_segments`
for exact local scenario edge IDs; if absent request baseline segments or explain the limitation.
Never invent a baseline edge ID from a graph node or OSM way ID.

Before traffic publication, a named settlement detour can be checked using the existing
`find_transport(kind=road, ...)` and `calculate_scenario(kind=connectivity, places=[...],
selection_ids=[...])` workflow from settlement-connectivity. Use qualified settlement names,
not reference-point addresses as settlements. This closes the resolved corridor, not necessarily
the sampled local segment: state that scope. It does not model one-lane capacity changes.
For exact local segment effects wait for a published traffic baseline and use municipal start.
Return short evidence and the next check; do not declare a bottleneck confirmed from candidates.

Use `municipal_analysis(action=overview, region_id=...)` to find municipalities with lower city
connectivity. Use returned municipality IDs for `indices` and `baseline`. Baseline returns saved
synthetic load, its coverage and way IDs; it does not generate data at UI request time.
Inspect load_quality: preliminary load keeps its measured relative_gap and converged=false.
It supports inspection and candidate selection, but routing_scenarios_ready=false forbids
claiming a lane-addition effect. A better published baseline is selected by lower measured gap.
Use `start` only with the returned baseline ID and selected way IDs, `change=capacity` for one extra
lane or `change=closure`. For a local closure, request `baseline` with selected `way_ids` to get
visible directed segments. Use `change=lane_closure` with exactly one returned `edge_index` in
`edge_indices`; choose its `reverse_edge_index` for the opposite direction. Closing the last lane
removes travel in that direction. For full closure of that segment, supply both returned edge IDs
with `change=closure`. Shared lanes allow only full segment closure. The segment sample covers
the published load overlay, not every road; use returned IDs only. Saved indices and the traffic
baseline are read-only; scenario results are separate. Propose lane additions only for corridors with `capacity_eligible=true`.
Read `capacity_reason` for excluded roads; they remain selectable for closures. Eligibility confirms
that the calculation supports the selected road, not land availability or construction permission.
Several roads selected for a lane addition must form one contiguous corridor; simultaneous closures
may be disconnected. Explain the three most relevant returned facts briefly. Call the metric «Связность с городами». Preserve negative/zero effects
and lost demand separately. Traffic totals cover the stored network, not only the municipality.
Completed municipal scenarios include local and regional city connectivity changes and municipal_effects.
Use municipal_effects for district road hours, overloaded edges and lost departures.
Baseline and scenario calls emit a map/result card; the UI polls and requests an interpretation when
finished. Return control after starting; use `status` when the user asks and `cancel` to stop.
A running job is not a verified effect. `assignment_progress` reports the last completed iteration
and its convergence gap, not completion percentage or remaining time.
Social accessibility is not recalculated until social_access_recalculated is true; road widening
never automatically improves walking access. Prioritize Stavropol and Krasnodar; Novosibirsk is the added Siberian pilot.
For demand_cell_km > 0, label the load as aggregated regional demand, not settlement-level
assignment. Use demand_zones to state its resolution; do not compare gaps across different demand resolutions as accuracy gains.

Use `access` for the selected municipality's deficit map, P90 and worst-decile mean.
Read the returned unit and unresolved/unreachable counts; these are reference points, not residents.
Facility search may cross regional borders. Use returned facility names and measured journey times.
For completed road scenarios, inspect `social_recalculated_criteria` and each
`municipal_effects.social` status. Only available criteria were recalculated on the changed loaded
network. Report lost routes, threshold crossings and time increases from those results.
`route_after_exists` confirms a path after this scenario, not an independent reserve route.
The affected-point sample is limited to ten; totals and `points_truncated` describe its coverage.
N01/N02 measure travel to known medical objects, without confirming cardiology or admission.
Walking and public transport access are not recalculated by the road scenario.

For a service-specific municipal priority list, use `overview` with `criterion_id`.
Items are ordered by confirmed exceeded-time reference-point share, descending.
The upper deficit bound also includes unmeasured points; do not present it as confirmed harm.
These shares describe reference points, not residents. Fully unmeasured municipalities rank last.
Use the returned threshold for `access` when opening the deficit map. `season` applies to city
connectivity; service travel modes and thresholds stay defined by their measurement model.

## Public transport journey

Use `municipal_analysis(action=transit, region_id=...)` for saved bus coverage and station coordinates.
Use `journey` with residential `origin_id` and `facility_id` returned by accessibility detail;
`departure_seconds` is seconds after midnight in the saved timetable's source clock.
The default is08:00; state the departure assumption when the user did not specify one.
The tool combines graph walking, waiting, scheduled rides and walking to the facility, and can
choose walking alone. Interpret returned legs and snapshot date; do not reproduce its internal matrix.
Current scope admits within-region timetable segments only and is incomplete. A missing journey
means none was found in covered data within the horizon, not that public transport does not exist.
Do not claim actual current operation, verified entrances, admissions or facility opening hours.
The map shows the origin, destination and used stops, using the same saved coordinates as the API.
The map event can be replayed from chat. These are journey points, not bus route geometry.
Do not infer which roads the bus takes from these markers. Missing coordinates remain absent.


## Regional closure

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
improvement mode is unavailable.

Read saved results with `manage_calculation(kind=status, calculation_id=...)`, use cancel to stop.
For saved national effects use `inspect_road_stress_test`; `compare_stress_route` checks a named
before/after route. Present returned road geometry once. Explain the important affected places,
verified time changes, lost alternatives and remaining routes in a short answer.
