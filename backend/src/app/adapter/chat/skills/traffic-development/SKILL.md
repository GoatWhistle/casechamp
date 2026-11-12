---
name: traffic-development
description: Find road changes that improve connectivity, divert transit around an area, or relieve congestion, with verified effects and map proposals.
---

# Road development

Use `calculate_scenario(kind=traffic_development)` as the sole search for road development.
Infer `objective` from the user's intended outcome:

| Intent | Objective | Lead with |
| --- | --- | --- |
| Connect places, add useful routes, improve access | `connectivity` (default) | Verified accessibility gain |
| Speed up travel through a city, find a faster bypass | `transit` | Travel time for the fixed baseline transit trips |
| Relieve busy roads or congestion | `congestion` | Verified load relief within the focus area |

Resolve named places with `query_atlas(kind=places)` or `kind=settlements`, using
region context to distinguish namesakes. Set the surrounding network context with
`bounds`, exact `region`/`regions`, one city in `places`, or two resolved endpoints. Preserve the requested
scope in one search, including links across regional borders.

For a named city, pass one resolved name/ID in `places`. The tool derives a focus
from residential data and retains the surrounding road context; do not ask the user
for coordinates by default. This focus is a residential envelope, not an administrative
boundary. Explicit `focus_bounds` overrides it when the user selects another area.

For transit or congestion, `focus_bounds` identifies where effects are measured;
outer `bounds` includes the surrounding routes and alternative paths. Resolve the
focus from returned stored geographic bounds or the user's map selection. A place
point is not an administrative boundary. When a required focus cannot be resolved,
ask for the area on the map; never invent coordinates, boundaries or transit flows.

Never propose an independent speed increase or speed multiplier. Extra lanes and widening must pass geographic screening. Speed on new roads follows their physical parameters; faster trips result from network changes and reassignment.

The tool selects and verifies extra lanes, geographically screened widening, closures, source-backed
openings, routed new corridors and compatible packages. Use its completed results,
objective effects, index values, affected roads and geometry. Report increased
loads alongside benefits. If the tool lacks data for the requested objective,
explain that limit; a connectivity gain alone does not establish transit relief.
Direct closure impact and criticality answer separate questions. Development
requests stay in this workflow rather than sensitivity or assumed queue tools.

Lead with the strongest verified proposal for the requested objective and its
concrete effect. Keep the explanation short and ordinary; technical algorithms
and internal model names belong outside the user answer. Existing changed roads
are red and proposed roads green. Reuse the displayed comparison and map instead
of duplicating tables or inventing alignments. Say "best checked option", not a
proven global optimum.

Generation runs before the separate300second verification stage and returns
completed proposals once. Initial data preparation may take longer. There is no
continuing optimization after the result. Use `manage_calculation(kind=status,
calculation_type=traffic, calculation_id=...)` to read results, `kind=cancel` to
stop, `kind=recent` to locate an ID, and `kind=traffic_data` to inspect sources.

For hypothesis-guided search, first inspect stored settlements and existing connectivity.
Optionally pass up to32 `hypotheses`, each with `source_place`, `target_place` and
`rationale`. Use exact returned settlement IDs; names are accepted only if unique
inside the requested area. Propose connections around a demonstrated detour or gap;
do not invent coordinates, travel times, speed multipliers or claimed gains. These
pairs supplement automatic problem discovery and pass the same geographic and
numerical verification. A hypothesis is never a recommendation until verified.
Generation has its own120second limit. Verification then receives a full300seconds;
input/baseline preparation and LLM reasoning are separate. Do not promise a five-minute
total response. No optimization continues after the returned result.
