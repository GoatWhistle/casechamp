# Average-load closure and durable agent results — 2026-11-11

User request: model average load, transfer it to detours, account for capacity and
queues, and stop the agent losing/fabricating previous scenario results.
Branch feat/map-first-ui, base SHA cdb2c2e1108bde7ff37ab91f9d7907d05de2a897.
No commits, pushes or paid model calls. Preserve the large concurrent dirty tree.

Implemented domain `traffic_diversion`: explicit 50% utilization, 1h closure,
1800 PCU/lane/h defaults. Adapter finds up to five edge-disjoint detours between
approach junctions, conserves modeled representative-direction flow, balances
travel times, adds a fluid queue at a bottleneck, then reroutes the selected
settlement trip on loaded roads. 2–4 selected places; pair experiments independent.
This does not model all regional OD demand or queue spillback; capacities and
background demand are assumptions, undirected legal routing remains a limitation.
See ../../docs/traffic-diversion.md for equations and precise scope.

Persistence root: GRAPH_DIR/connectivity-results. Immutable JSON, atomic rename,
UUID, UTC, graph/model versions, exact closed ways. Readable after resolver/process
restart through manage_calculation status/recent. Economics reads the same saved
traffic result and computes conditional transit-cohort time cost, not GDP/total loss.
History includes calculation IDs, including answers that consist ONLY of artifacts:
use-map-chat formerly filtered those out, caught by real browser request replay.

Checks:
- Red reproduction test_connectivity_memory initially failed: missing calculation_id.
- 374 backend unit tests; Ruff; mypy 258 files; 46 ClickHouse integration tests passed.
- FunctionModel two-turn typed tool protocol: load skill, calculate traffic, new
  agent/resolver reads saved economics, exactly one saved calculation; no paid LLM.
- Frontend verify: 36 rules, types/lint, 461 tests, build passed. Existing chunk-size
  and PostCSS warnings remain. Repeated verification only after fixes/changes.
- Browser1440 real-result NDJSON replay: summary assumptions, queue columns,
  reload, actual next request preserves ID; page errors0, axe0. Screenshots inspected.
  No mobile checks per protected user instruction.
- validate.py reads real ClickHouse graph and actual tools, saves result/economics/events.
  Exact bridge ways37787244/133175822. Pair19.8294→24.7616min, flow1800PCU/h,
  queue638.1534PCU, transit loss1345.2979PCU-h, assumed500RUB/PCU-h gives672648.94RUB.
  Scope one representative direction; not all bridge users or calibrated actual losses.

Failed checks resolved:
- First validation used external way IDs against cost_profiles keyed by internal
  way_idx; fixed explicit mapping and covered by real graph validation.
- First draft forced local NP trip through bridge approach portals. Fixed by placing
  detour loads in graph and independently rerouting NP pair. Regression diamond graph
  proves local trip can bypass portals. Superseded own result moved from runtime to
  superseded/ to keep agent recent list from exposing that invalid development run.
- Frontend rule rejected middle-dot unit; changed to plain automobile-hours label.
- Browser wait registered after click raced the response; register before click.
- Next browser run proved table-only history was discarded; fixed actual filter and
  added regression at historyOf seam. Final browser request test passed.

Artifacts: result.json, economics.json, events.json, selection.json, bridges.json,
validation.log, unit.log, integration.log, frontend-verify.log, browser-checks.json.
Product-sized protocol: ../../docs/results/traffic-diversion-validation.json.

Runtime update: waited until existing Tver/Novgorod regional jobs finished, then
stopped API1751 gracefully and started updated API14139 on8007 with ROAD_WORKERS6,
CHAT_ENABLED=true, log /tmp/plexus-traffic-api.log. UI5187 unchanged.
Health confirmed HTTP200 after startup; UI requests to the updated API return200.
No required work remains for this scoped scenario model. Free-form paid LLM behavior
was not tested; deterministic typed-tool protocol and actual UI history were tested.
