## Saratov analysis failure diagnosis, 2026-11-12

User reported improvement analysis stopping at 0/10. Exact matching job
fb2880ec02634e53a2e2c0f091610cae found in /tmp/plexus-table-api.log: region63000000,
improvement20%; ClickHouse HTTP500 during screening candidates read, before road
verification. Raw database error body was not retained, so SQL/root storage cause
is unconfirmed. UI uses generic saved-results wording even at zero results.
Read-only diagnosis; no product changes or tests. API8007 currently unavailable.
feat/transport-scenarios-update HEAD986ae0f5ee754b9e98f25e2e608b5bc37cbad507.
Next: reproduce candidates query against active storage and inspect server error;
then fix confirmed cause and distinguish empty failure from partial results.

## Hackathon decision scenario proposal, 2026-11-11

User requested remaining work for a compelling hackathon result, then supplied a
consultation screenshot. [Source and exact replies](../brief/QA.md); speaker/date unknown.
[Revised proposal and preserved user wording](../work/hackathon-decision-plan.md):
regional access, disruption vulnerability and intervention effect; small-group scores
are drill-down, not the main product. Define market/self contribution and comparable
scenarios before implementation. Current edit_selection uses the open baseline.
Proposal only; no product changes, model calls or new runtime checks.
feat/map-first-ui HEAD cdb2c2e1108bde7ff37ab91f9d7907d05de2a897. Next if requested:
fix metric/decision specification, then implement common experiment comparisons.
Further user guidance: choose concrete trips before metrics; revenue is not transport
quality, school access is an example. Exact wording and implications are preserved at
the top of the decision plan. Keep route time/path availability explicit beside scores.

## Agent capability review, 2026-11-11

User: «изучи что уже умеет ии агент и что мы умеем считать».
Reviewed working code, bundled analyst skills and numerical evidence. 93 focused tests
passed; read-only API confirmed health, 82 regions and 180 markets. No paid model run.
feat/map-first-ui HEAD cdb2c2e1108bde7ff37ab91f9d7907d05de2a897; product unchanged.
[Capabilities, gaps, limits and next actions](../work/agent-capabilities-review.md).
