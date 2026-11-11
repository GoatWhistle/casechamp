# National road stress test implementation

User approved national road-only stress tests, map and agent parity, route comparison,
compound closures, persistence, progressive presentation and polished desktop UI.
Do not narrow to a pilot region. Do not collect traffic or add construction projects.
Plan in conversation is authoritative. Preserve all unrelated uncommitted changes.

Implemented so far (not release complete):
- Separate StressJobs on the existing RoadJobs queue, unlimited road searches to all markets.
- National aggregation, point exposure, road-only before/after route geometry and km.
- New typed API /road-stress-tests, lazy ClickHouse store, additive schema/migration script.
- Agent tools and stress_test NDJSON event, frontend history/card support.
- Initial map overlay and manual card, locality name search, progress and cancellation.
- Five domain unit tests passed. New backend modules Ruff/mypy passed.
- ClickHouse schema applied locally via backend/scripts/migrate_road_stress.py.
- Real points query: 155747 points, 84 source regions, population 128796185.

Still required before claiming completion:
- Durable national baseline cache and per-market changes, early connectivity phase.
- Complete selection/active-scenario context for agent, route artifact rendering, map
  national region aggregates, closed-way geometry, bound-driven point layer, map click drilldown.
- Comparison navigation across parent scenarios; active chat/map state isolation.
- Result history validation and complete route selection behavior.
- Integration tests including parallel edges, >72h path, compound closures, stored reload.
- Run full frontend verification, backend checks, actual national benchmark and desktop E2E/visual QA.
- Current frontend card is a first functional pass, not final polish. No deployment/restart yet.

The first npm api:types invocation failed resolving registry.npmjs.org. Generated successfully
using cached /Users/andreykuronskin/.npm/_npx/f1e70922fc87e24a/node_modules/openapi-typescript/bin/cli.js.
Some sandboxed TypeScript executions hang; escalated tsc returned useful diagnostics.
No paid model calls performed. No commits/pushes.

## Verification and environment update

Backend Ruff/mypy passed, 328 unit tests passed before adding three more mathematical cases.
Eight focused domain/route tests now pass, including parallel ways and >72h paths.
Frontend 36 rules/typecheck/lint passed; after disk cleanup all 451 tests and build passed.
A persistent numerical baseline cache in ClickHouse and active-selection context for the
agent were added. Closed-road geometry and national region overlays were added afterwards;
these latest changes still need the final verification pass.

Disk reached 100% free ~109MB, breaking ClickHouse and temporary test files.
User explicitly approved deleting Library/Caches/{JetBrains,Google/Chrome,pip,go-build}.
JetBrains/pip/go-build removed; Chrome recreated part of its cache while running.
Free space recovered to 6.1GiB. Do not delete project backups or data.
User explicitly approved restarting Docker Desktop. Normal restart timed out, SIGTERM
stopped all except backend PID7324; that remaining unresponsive Docker process was killed
and Docker reopened. Await Engine recovery before migration/integration/national checks.
ClickHouse migration for stress_baseline and storage test have NOT passed yet due daemon outage.
No national test has run. Script work/road-stress/verify_national.py is guarded for spawn.
