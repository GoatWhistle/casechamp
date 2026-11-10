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
