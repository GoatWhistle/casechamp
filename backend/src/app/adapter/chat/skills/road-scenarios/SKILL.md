---
name: road-scenarios
description: Calculate road closures, speed or lane changes, new connections, bridge scenarios and searches for regional improvements.
---

# Calculate road scenarios

Read `query_atlas(kind=capabilities)` for active model rules and tool availability.
Use real returned IDs. Explicit locations override the selected map region.
An authorized model scenario can be started without repeated confirmation; source
data is unchanged. Ask only about concrete ambiguities or missing scenario inputs.

For selected settlements, center access, traffic redistribution or overloaded
detours, load `settlement-connectivity`. It owns group scores, traffic assumptions
and saved-result follow-ups. National stress and ordinary network scenarios use
fixed road weights; describe their route times accordingly.

For road closures, resolve corridors/bridges with `find_transport`, then call
`calculate_scenario(kind=close_selection, selection_ids=[...])`. Default assessment=impact
starts regional Hansen for the selected corridor regions together with nationwide road-only consequences.
Use region_ids to include additional requested regions. One response contains indices and consequences;
read both and explain their business significance according to the question. For selected map ways, call `stress_test_roads`
with way_ids from context and empty selection_ids. Pass parent_id only for an explicitly
requested additional closure. Source data is unchanged.

## Explain what changes in a region

Read `inspect_road_stress_test(job_id, region=...)` using the requested region's
exact atlas name or ID. For "this region", use context.region_id. Use the saved
context.stress_job_id when it matches the closure; use `query_atlas` if region
identity is unclear. Inspect each requested region separately. The joint closure
remains joint; individual-road attribution requires separate scenarios.

If history only contains a legacy regional calculation ID, call
`stress_test_roads(way_ids=[], selection_ids=[], source_calculation_id=<that ID>)`.
This reuses its exact saved closure and an existing identical stress test where
available. Then inspect the returned stress job by region. Pending means wait for
the live card; this does not turn a Hansen percentage into operational effects.

The evidence bundle contains regional indices, an affected-region overview, named market
connections, delay exposure, nearby-access changes and matching saved traffic scenarios.
Use it to find consequential business effects, including local losses hidden by a regional
average. Select what deserves attention; keep the rest for follow-up. Make inferred effects
on deliveries or market reach conditional on businesses using the affected routes.

For congestion questions, one `close_selection` request can also include `places` (2–4
settlements) and `traffic={}`. This computes an explicitly assumed-load pair scenario alongside
the index and national consequences. Load `settlement-connectivity` for parameters and scope.
The user's request for modeled congestion permits labeled assumptions, not claims about
observed traffic. Empty saved traffic evidence means unmodeled, not uncongested. Queue results
locate pressure on modeled OD detours, not exact real-world intersections. Suggest a new
connection or road improvement when the evidence motivates it; calculate it before claiming
benefits or calling it optimal. The user can request alternatives and details afterwards.

Regional consequences include nested 30/60/120 minute exposure thresholds, lost nearby links,
means for the SAME changed surviving connections (with comparable_connections), destinations
and examples with before/after minutes. Null after means no modeled path. These are not all
regional trips; exposure counts residents, not road users. Avoid adding overlapping groups.

This is a conditional network forecast for the exact saved closure: road-only,
fixed weights, no traffic queues. Only recorded changes (>=1 minute or lost path)
are included. Population is counted once within a metric, not across destinations.
New loss of all external model markets is not proof of physical isolation.
Use `compare_stress_route` with resolved point IDs if actual detour km/map is needed.
For load/queue scenarios, load `settlement-connectivity`.

Hansen is included by default, using the active atlas network and normalization; road-only
consequences use a distinct network. Compare the before/after values within each method.
For an older saved stress test missing indices, use
`stress_test_roads(way_ids=[], selection_ids=[], source_stress_id=..., region_ids=[...])`.
This reuses the exact closure and computes missing regional indices, without re-resolving
expired selections. Choose regions from the user's scenario, not an unrelated map selection.
`assessment=hansen` is available when only the index is needed.
Use `kind=network` for mixed transport edits. Read active model rules before interpreting results.

For a road identified by two endpoints without a specific road name/number, use
`find_transport(kind=road)`. It searches the complete connected road graph from both ends,
including differently tagged and unnamed roads, and returns a corridor ID usable by
`calculate_scenario(kind=close_selection)`. Do not invent a highway number or demand one from the user.
It selects the fastest model road route, not all routes between the places. Whole
selected OSM ways can extend beyond the exact path. No virtual gap is used. The
returned time includes attachment distance at the model's approach speed.
If a named-road lookup fails, this tool can inspect a connected alternative, but
do not claim the alternative is the requested highway without matching evidence.
When an endpoint is ambiguous, use the user's specified or selected region to
qualify the name if consistent with the request. Ask only if several choices remain.

For a named highway between places, use `find_transport(kind=road, road_name=...)` across the full graph,
then `calculate_scenario(kind=close_selection)`. Full closure means both directions, other roads unchanged.
The impact assessment evaluates the national snapshot. Resolve several corridors,
then submit all IDs together for their joint effect. Normalize road references.
Qualified place candidates can resolve an ambiguity; do not repeat an unresolved
call unchanged or substitute a whole highway for a requested bridge.

For speed changes on named roads or resolved routes, pass all corridor IDs together:
`calculate_scenario(kind=edit_selection, selection_ids=[...], speed_factor=1.2)`.
The server expands and deduplicates all road ways and queues regional index calculations.
Never request, enumerate or reconstruct way IDs for a resolved selection. Missing way IDs
in a search reply are intentional, not missing data. Use the returned IDs directly.
This starts from the open base network, independently of earlier closures. A factor of
1.2 increases speed by 20%; changed-edge travel times become 1/1.2 of baseline.
Report actual index results after completion; do not claim a door-to-door route-time
comparison from regional index results. The existing live calculation card handles progress.

For bridges, search `find_transport(kind=bridges)` near the named settlements, then pass all
selected bridge IDs to one `calculate_scenario(kind=close_selection)`. Search from both sides of an
interregional bridge. Candidates may include overpasses and parallel carriageways.

`find_transport` and `calculate_scenario` use a typed request object with kind and the relevant fields.
For explicit way edits, `find_transport(kind=road_viewport)` supplies OSM IDs within a viewport; its
sample is not the full network. Use the full-graph corridor/bridge tools when applicable.
`calculate_scenario(kind=network)` accepts region_ids, road_changes and links in one scenario. A speed factor of 1
leaves time unchanged, 1.2 increases speed by 20%, 0 closes the whole OSM way.
Alternatively set lanes, class, surface or design speed with speed_factor=1.
For these network profile edits, lane count changes capacity; delay needs confirmed hourly flow. With
unknown flow, widening alone leaves free-flow time unchanged. Missing lanes use one
per direction. Class/surface/speed changes can alter time without measured traffic.
Do not infer a widening bonus or road flow from population or appraisal trips.

For a new connection, resolve real node IDs with `find_transport(kind=graph_places)`, then
`calculate_scenario(kind=connection)`: one bidirectional link on the base network, explicit hours
between attachment nodes, not door-to-door time. The fast delta path is for this
addition; closures and other edits use full routing. Cold preparation takes time.

For broad improvement searches use `calculate_scenario(kind=road_analysis)` with its default +20%
speed assumption, stating that assumption rather than demanding individual IDs.
The live ranking and final commentary appear in chat; do not send the user to another
page. Best checked candidates are not proven global optima. Uniform-time sensitivity
is a separate experiment, not the infrastructure effect.

Report queued/running jobs as pending. Read `manage_calculation(kind=status)` for actual
results without busy-polling. Load `economic-assessment` for monetary effects and
preserve the recorded baseline/version of each job.
