# Project context

Plexus: transport accessibility for regional policy analysts. Population-weighted
Hansen market accessibility and network scenarios for all 82 atlas regions.
Russian UI, one light theme; no mobile checks. Current worktree: casechamp-normative-indices, branch docs/normative-indices-plan; original worktree preserved.

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
derived numerical caches retained. API8001 requires `.env.analytics`; GRAPH_DIR is cache root.
Evidence and limits: [storage and performance](../docs/clickhouse.md).
Source and data published to feat/map-first-ui and release data-clickhouse-20261110.
87 tables/2.76GB verified; restore instructions: [ClickHouse](../docs/clickhouse.md).
Final checks and source checkpoint: [SESSION](SESSION.md). No deployment performed.

Normative map,2026-11-12: Compose8083/API8003. Nine metrics/84territories,30legal bases;754/756numericpairs (352conditionalbasis,402separate scenarios). Eightcriteria84each; bus-terminals82, no objects forNenets/Chukotka. Fire84assumed40km/h. OfficialCZN84directories/2406deduprecords/2229located,84successfulofficialcalculations; Altai corrected with65regionalCZN. No confirmed legalcompliance. [Proof](../docs/results/normative-national-scenario-validation.json), [coverage](../docs/results/normative-live-index-coverage.json). Fullgoal incomplete: legalcoverage, verifiedinputs, actualparcel/stop measurement. [Checkpoint](../work/normative-session-history-2026-11-12.md#national-scenario-indices-after-direct-calculation-request).
