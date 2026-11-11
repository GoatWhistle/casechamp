---
name: settlement-connectivity
description: Compare selected settlements, model closures and overloaded detours, or continue a saved connectivity calculation.
---

# Selected-settlement scenarios

## Calculate

1. Take the user's settlement names; qualify ambiguous names by region.
   Use 2–12 places, or 2–4 with traffic. Default `mode=all_pairs`;
   `to_center` requires `center` exactly matching one selected name.
2. For a closure, resolve the intended bridge/road with `find_transport`.
   Pass all selected IDs together. An ambiguous bridge needs clarification;
   an expired selection needs resolving again.
3. Call `calculate_scenario`:

```json
{"request":{"kind":"connectivity","places":["<origin>","<destination>"],"selection_ids":["<resolved ID>"],"traffic":{}}}
```

Use `traffic={}` when the user requests modeled load, congestion or overloaded
detours. Defaults: 50% utilization, 1 hour, 1800 PCU/lane/hour. Override supplied
values through `utilization`, `duration_hours`, `capacity_per_lane_pcu_h`.
Omit traffic for fixed-weight routing. Empty `selection_ids` means no closure.

## Continue

Use the exact `calculation_id` from displayed history:

| Need | `manage_calculation` request |
| --- | --- |
| Read result | `kind=status`, `calculation_id` |
| Inspect road IDs | Same, plus `detail=full` |
| Cost of saved traffic | `kind=connectivity_economics`, `calculation_id`, `value_of_pcu_hour_rub` |

Use `recent` only when the ID is missing; match places and closure. Reuse saved
results. For monetary assumptions and scope, load `economic-assessment`.

## Answer

Lead with the effect. Tables already show the numbers: explain the meaningful
change, state traffic assumptions, and mention the relevant limit. Keep internal
IDs in tool calls unless requested. A pending/error result has no final estimate.

- Score: equal pair average of `100 × 2^(−hours/2)`, not regional Hansen.
- `unreachable`: zero score; `unbound`: unknown, including the group score.
- Traffic: all modeled flow is assigned or reported unserved. Queue is separate
  from assigned flow. Unknown lane counts are reported as counts in the summary.
- Pair trip time and transit detour time describe different journeys. Use saved
  `time_loss_pcu_hours` for transit cost, not the pair's time difference.
- Each pair models one representative direction independently. Do not sum pairs.
  Scope: point attachments, undirected roads, up to five disjoint detours;
  no spillback/signals, seasonal additions, rail or air. Label estimates as modeled.
