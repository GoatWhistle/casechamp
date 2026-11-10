# Road analysis implementation

Implemented 2026-11-10, feat/map-first-ui, base HEAD 63fb9cb. No commit/push/deploy.

Complete: whole-way geography and topology/path screening, exact 180-market verification,
separate criticality rankings, durable batches of ten, cancel/continue/recovery,
shared manual executor, API/chat tools and Scenario UI with history/details/map.
Added full-graph named corridor resolution and closure jobs for both endpoint regions.
Updated original local API8001 and frontend5187. Test API8002/frontend5188 also running.

Verification: frontend verify passes 36 rules, typecheck, lint, 379 tests and build.
Backend Ruff/mypy (117 files) and 52 focused unit/integration tests pass.
Full backend suite has five preexisting stale catalog-count assertions; not fixed.
Desktop1440/1920, keyboard/reduced-motion and axe pass, no browser errors.
Four real first-candidate cases (Volgograd/Tuva x improvement/criticality) completed.
Evidence: docs/road-analysis.md and docs/results/road-analysis-validation.json.

Outstanding validation limits: no real complete ten-candidate batch timing,
no independent rerun of four exact candidate results, no paid model request,
no end-to-end Кавказ closure calculation. Direct corridor search resolves 190ways.
No mobile checks per user preference. UI manual jobs now selectable from history.

## Prior implementation state (preserved)

Branch feat/map-first-ui, HEAD63fb9cb44f4fe53ce16c7d64e571bca234fb0135. Prepared84snapshotregions/82mapregions/180markets, persistent268MBmatrices+228MBCSR, eagerlyloaded at backend startup. Single added bidirectional edge exact delta:30mscompute/0.42sAPI on prepared city endpoints; fullgraph independent match within2.44e-7. Arbitrary endpoints need first search then persistent cache. Closures/speed edits/seasonal scenarios still fullgraph. Added agent location/addition tools, conditional money by explicit OD/trips/rate, purple hypothetical line. Graph sampling/viewport gaps fixed; previous geometry retained during zoom. Evidence and limitations: work/screens/road-graph.md. Backend8001/frontend5187 running. No commit/push/deploy or paid model call. Next: user review; general multi-edge incremental routing remains unsupported.
