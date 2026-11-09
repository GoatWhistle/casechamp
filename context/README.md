# Project context

Plexus: transport accessibility for regional policy analysts. Two levels: population-weighted
Hansen market accessibility for 82 comparable regions, and interactive centre trips in Tuva.
Russian UI, one light theme; no mobile checks. Work on main, small commits, preserve root HTML.

## Current facts, 2026-11-09

| Topic | Status | Evidence |
| --- | --- | --- |
| Plan | active | [Full delivery plan](../work/project-plan.md), revised after correctness review. |
| Git | local commits | Release1 source4b37636; model, API/UI, national exports, Compose, docs and defense committed locally; not pushed. |
| Pilot | verified on local stand | 7 points, 19 edges, 3 pairs; 24 same-graph independent comparisons. [Method](../docs/pilot-method.md), [reports](../docs/results/pilot-validation.json). |
| Pilot effects | conditional model results | Kungurtug–Kyzyl: base 18.095h; frequency 4 has zero effect; frequency 7 gives 14.243h. Historical service and OSM operability remain unverified. |
| API/UI | verified locally | 137 unit + 6 integration =143 backend checks; frontend 375 tests/36 guards; four desktop Playwright scenarios passed on clean and scrubbed Compose checkouts. |
| Compose | healthy | Two services, mounted read-only artifacts, no paid keys. Port 8081 runs Compose; 8000/8080 dev services remain live. |
| Inputs | restored | Seven tabular sources, ten PBFs and extracted Parquets. PBF source timestamp 2026-11-07T21:21:36Z. data/ is ignored; manifests retain hashes. |
| National graph | built | 6,991,438 nodes, 17,395,685 edges; 155,747 points in source. Comparable index excludes 335 partial federal-city points, leaving 155,412 in 82 regions. |
| National index | verified and published locally | 410 rows/5 scenarios, 777060 point rows; road mean=100, zero monotonicity violations, 12 independent formulas. Artifact 7868caee. [Protocol](../docs/results/national-validation.json). |
| Defense | rendered and inspected | Seven HTML slides, two-page passport and two-page speech PDF under docs/submission/. Speech 561 words, estimated 269s at 125 wpm; not a live rehearsal. National values refreshed; PDFs inspected, all seven slide PNGs checked. |
| Submission | not sent | Primary deadline reply: 10 Nov 23:39; timezone unknown. Chat synced through message 270 on 9 Nov 06:22 UTC, submission form not found. Team fields intentionally blank at user request. |

## Pointers

- [Protected instructions and current session](SESSION.md)
- [Unresolved external facts](open-questions.md)
- [Detailed progress and process notes](../work/implementation-progress.md)
- [Original requirements](../brief/requirements.md)
- [Initial alignment audit](../work/audits/project-alignment/2026-11-09.md)

Next: submission form and explicit team submission authorization; live speech rehearsal and external transport validation. Local plan work is complete. Clean submission copy/history passed verification without changing main; local archive is prepared under tmp/.
