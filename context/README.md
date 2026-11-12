# Project context

Plexus: transport accessibility for regional policy analysts. Population-weighted
Hansen market accessibility and network scenarios for all 82 atlas regions.
Russian UI, one light theme; no mobile checks. Work on feat/map-first-ui, preserve uncommitted work, preserve root HTML.

## Current facts, 2026-11-09

| Topic | Status | Evidence |
| --- | --- | --- |
| Plan | blocked on external submission | [Full delivery plan](../work/project-plan.md), revised after correctness review. |
| Git | local commits | Release2 source4915346; model, API/UI, national exports, Compose, docs and defense committed locally; not pushed. |
| API/UI | verified locally | Backend 143, frontend 375 tests; four desktop E2E scenarios passed. |
| Compose | previously verified | Two services; see stand protocol. |
| Inputs | restored | Seven tabular sources, ten PBFs; manifests retain hashes. |
| National graph | built | 155,412 comparable points in 82 regions. |
| National index | verified and published locally | 410 rows/5 scenarios, 777060 point rows; road mean=100, zero monotonicity violations, 12 independent formulas. Artifact 7868caee. [Protocol](../docs/results/national-validation.json). |
| Defense | prepared | Seven slides, passport and speech; no live rehearsal. |
| Submission | not sent | 10 Nov 23:39; timezone unknown, form not found in last chat sync; team fields blank by user request. |

## Pointers

- [Protected instructions and current session](SESSION.md)
- [Unresolved external facts](open-questions.md)
- [Detailed progress and process notes](../work/implementation-progress.md)
- [Original requirements](../brief/requirements.md)
- [Initial alignment audit](../work/audits/project-alignment/2026-11-09.md)

Next: route validation, sensitivity, submission and rehearsal.

Workflow: feat/model-validation; source c5dc29e. Publishing local commits and validation evidence to the same remote branch. Final readiness: work/release-readiness.md.

Implemented/locally verified: runtime reads use ClickHouse for atlas, graph, matrices and jobs.
124 migrated source files (2.37GB) deleted after equality checks and no-source API restart;
derived numerical caches retained. The local API now uses8007 and requires `.env.analytics`; GRAPH_DIR is cache root.
Evidence and limits: [storage and performance](../docs/clickhouse.md).
Source and data published to feat/map-first-ui and release data-clickhouse-20261110.
87 tables/2.76GB verified; restore instructions: [ClickHouse](../docs/clickhouse.md).
Final checks and source checkpoint: [SESSION](SESSION.md). No deployment performed.

2026-11-11: road-capacity-v1 implemented and activated locally, 82publicregions×3scenarios
(246records), 84sourceregions/467241pointrows. Missinglanes1perdirection; unknownflowfreeflow.
Routedfreighttime/km and passengerappraisal use updatedroadweights. API8007, UI5187,
300backendunit/45integration/448frontend/3desktopE2Epassed. [Method+limits](../docs/road-capacity.md),
[checks](../docs/results/road-capacity-checks.json). Prior410-row5-scenario v2artifact is historical.

2026-11-11: analysttools unified to6interfaces,2initial; schemasloadwithskills.
Locallyverified323backendunit/45integration/448frontend. [Contract](../docs/chat.md),
[evidence](../work/unified-agent-tools/README.md). API8007PID77015, no paidLLMrun.

2026-11-11: national road stress implemented and locally checked on155747points/180markets.
Three closure runs, persisted baseline/details, map+agent cards and real detours.
[Method/evidence](../docs/road-stress.md); [latest checks and runtime](../work/road-stress/README.md).
Separate validation UI5190/API8817, primary5187/8007 unchanged. No paid agent evaluation.

- Implemented/tested 2026-11-11: assumed-load closure detours/queues, durable
  connectivity IDs and saved-result economics; [method](../docs/traffic-diversion.md),
  [validation](../docs/results/traffic-diversion-validation.json). One representative
  direction, independent pairs, no spillback; no free-form paid model validation.

- Implemented/verified 2026-11-11: concrete regional closure consequences (delay
  thresholds, nearby links, comparable before/after times, named connections),
  shared by API/agent; [method](../docs/road-stress.md),
  [checks](../docs/results/regional-consequences-validation.json).

2026-11-12: implemented/locally verified synthetic traffic CLI and bounded project screening.
National residential OSM collection stored in separate local CH database; pilot models tested.
[Method and limits](../docs/synthetic-traffic.md), [evidence](../docs/results/synthetic-traffic-validation.json).

2026-11-12: verified agent road proposals with Plexus indices, chat results and road overlays. [Evidence](../docs/results/traffic-agent-validation.json).
