---
name: settlement-connectivity
description: Evaluate connectivity between 2-12 selected settlements or to a center, including before and after road or bridge closures.
---

# Evaluate selected settlements

Use `calculate_scenario` with `request.kind=connectivity`. Supply `places` as exact
settlement names qualified by region when needed. The tool resolves names against
the graph snapshot and rejects ambiguity and duplicate resolved IDs. The selected
map region does not replace the user's explicit places.

Use `mode=all_pairs` for mutual connectivity: 2/3/4 places produce 1/3/6 pairs.
For access to a center, use `mode=to_center` and `center` exactly equal to one entry
in `places`. The remaining entries are origins. Self-pairs are excluded.

For closures, first resolve the user's road or bridge with `find_transport`.
Pass all returned `selection_ids` in the same connectivity request. This closes
their whole OSM ways in both directions and reroutes each pair under the same closure set.
Keep the same places and mode for before/after. A road identified only by endpoints
selects the fastest baseline route's ways; alternatives stay open. Ask about an
ambiguous bridge rather than substituting an entire road. Historical selection IDs
may expire on restart; resolve them again if the tool reports an unknown selection.

The tool returns actual computed results and displays summary and pair tables.
Explain the lowest-scoring pairs, detours and newly disconnected pairs from those
results. Use table values for arithmetic; no hand-authored replacement scores.
An unchanged result is valid if the closed roads do not affect these pairs.

The fixed score is `100 * 2 ** (-travel_hours / 2)`, averaged equally over selected
pairs. It is a project-defined time-accessibility score, not regional Hansen or
a percent of transport quality. Two hours gives 50, four hours 25. Keep the two-hour
scale fixed when comparing scenarios. There is no own-city population contribution.
Different selected groups answer different questions; name the group and mode.

`unreachable` means no road path in this snapshot, scores zero and stays in the
denominator. `unbound` means missing/invalid road attachment: the pair and overall
scores are null, not zero. Neither proves physical isolation. Show missing data.
This version uses the baseline undirected road graph with existing lane/time weights
and attachment travel at 15 km/h. It excludes seasonal additions, rail and air;
state that scope even if the map has another season or transport mode selected.
The calculation is hypothetical and never changes source road data.

## Traffic and durable follow-ups

When asked about load, congestion, narrow detours or to assume average traffic,
include `traffic={}` in the connectivity request. Defaults are explicitly modeled
50% utilization, a one-hour constant-demand closure and 1800 PCU/lane/hour.
Override `utilization`, `duration_hours` and `capacity_per_lane_pcu_h` if supplied.
Do not demand measured traffic when the user has authorized modeled assumptions.
Do not call a free-flow calculation a traffic forecast. `traffic=null` is the
no-redistribution comparison and must be labeled accordingly.

The traffic model transfers the assumed flow on the closed baseline corridor to
up to five edge-disjoint detours between its approach junctions. It uses each
route's bottleneck lane capacity and existing background load, balances travel
costs across the candidate routes, and accumulates a fluid queue when demand
exceeds capacity. It caps the moving-time BPR term at saturation, then adds queue
waiting; it does not add an unsupported capacity drop. All assigned demand is
accounted for; if no route exists it is unserved, not zero delay. Traffic on
closure components outside the selected baseline route is outside this estimate.
Each pair is an INDEPENDENT representative-direction corridor experiment; do not
sum pair flows, queues or costs or claim a national equilibrium. Unknown OSM lane
counts use explicit narrow-road assumptions. The network remains undirected;
it does not validate legal one-way routes or model queue spillback/signals.

Read `traffic` on each pair for assumed demand, split flows, bottleneck capacities,
queue and waiting time. Pair times are the fastest settlement-to-settlement path after placing the
assigned flows and mean bottleneck waiting on detour edges. The transit cohort
uses bridge approach junctions as its endpoints, not the settlement centers.
Its mean detour time and time loss are separate from the pair's trip time;
do not multiply settlement time changes by transit traffic to invent a cost. Show the assumption and closure duration
alongside any time/index claim. Values are scenario estimates, not observed traffic.

Every successful calculation returns `calculation_id`, timestamp, graph/model
versions and exact closed ways, persisted before the tool returns. The summary
table row carries this ID into subsequent chat history. For "and economically?",
use THAT ID with `manage_calculation(kind=connectivity_economics, calculation_id=...)`.
This reads the saved result and computes the cost; it does not rerun routing.
The default 500 rubles/PCU-hour is an illustrative composite assumption, not wages
or a market rate. State it, and use a user-supplied rate instead when available.
The result covers diverted-cohort time only, excluding other road users, fuel and
cargo losses. Never present it as all losses, GDP or revenue. Null cost for an
unserved pair is incomplete evidence, never zero. Load economic-assessment too.

Use `manage_calculation(kind=status, calculation_type=connectivity, calculation_id=...)`
to verify any prior result. Use recent only to locate a missing reference, matching
places, closures, timestamp and model; do not silently choose an unrelated latest
calculation. Missing old results cannot validate previously asserted numbers.
