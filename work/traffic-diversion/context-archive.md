# Prior session details, preserved verbatim

## Current state

Road capacity integration and activation completed locally on2026-11-11.
Full measured state and rollback details moved unchanged to
[capacity archive](../work/road-route/session-before-route-compaction.md).
Maintain unknown-flow free movement and preserve the larger inactive refresh graph.
[Capacity runbook](../work/road-capacity/README.md). Latest API/task state below.

## Capacity and product value review, 2026-11-11

Capacity activation is complete; lane-only changes have zero benefit without confirmed
traffic. Traffic research was cancelled: do not resume it without a request.
Value review and all prior details: [review archive](../work/usecase-review/context-detail.md).
No measured customer ROI or causal GRP claim. Preserve uncommitted work.


## Settlement map focus, 2026-11-11

Implemented `present_atlas(kind=settlement)` with server-owned coordinates, parent region,
named marker, replay and reduced motion; no added tool. Full state and failed-check history:
[settlement focus](../work/settlement-focus/README.md). Branch feat/map-first-ui HEAD cdb2c2e.
Ruff/mypy,335unit,46ClickHouse integration,frontendverify453tests passed; 2desktop functional
E2E passed on build. Screenshot inspected; no mobile/paid model run. No commit/push/deploy.
API8007 restarted idle, PID96218, health200 and updated schema; UI5187 unchanged.
No required work remains for settlement focus. Preserve concurrent unfinished road stress work.


Area-model review: current pair times are one node per settlement, not road-node sets.
Recommend fixed spatial samples with explicit weights, full-network rerouting and
reachability reporting; avoid minimum boundary time/free internal connections.
[Evidence and proposed method](../work/settlement-connectivity/README.md#area-representation-review-2026-11-11).
No model change. feat/map-first-ui HEADcdb2c2e. Next: assess settlement boundaries.

Closure congestion review: confirmed closed ways are removed but detour flow/weights
are not reassigned. The displayed +2.7min is fixed-cost routing, not post-closure
traffic prediction. [Evidence](../work/settlement-connectivity/README.md#closure-congestion-limitation-2026-11-11).
No model changes; traffic search remains cancelled. feat/map-first-ui HEADcdb2c2e.

