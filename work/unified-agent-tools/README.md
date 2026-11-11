# Unified analyst tool interface

2026-11-11. User requested one coherent interface instead of accumulating model tools.
Branch feat/map-first-ui, source base cdb2c2e; uncommitted work preserved. No commit,
push or remote deployment. Supersedes the earlier eager registration in agent-skills.

Model-visible tools: load_skill, query_atlas, find_transport, calculate_scenario,
manage_calculation, present_atlas. Initial step exposes only the first two. Loading
road/rail-air/economic skills enables the transport trio; presentation enables the
last tool. Text and actual schemas are disclosed on demand via PrepareTools. State
is stored per ChatRun and does not leak between requests. No keyword routing or
fixed answer substitution. Main/analysis commentary still cannot start new jobs.

Typed request variants replace separate operations. Optional road_name selects the
named-highway implementation; otherwise bidirectional endpoint routing is used.
Network scenarios combine road and service edits with the existing regional appraisal.
Selection closure retains bridge grouping and all joint corridor IDs. Existing math,
ports, HTTP schemas, databases and saved jobs are unchanged. Internal operation helpers
remain reusable; their old methods are no longer registered with the model.

Strict request dataclasses live only in the chat adapter and convert to ordinary
use-case/domain DTOs. Unknown fields (including unimplemented frequency edits) are
rejected. Road changes through the common network submission preflight geometry and
emit the same calculation artifacts. Frontend status labels support the six names;
legacy labels remain for stored conversation history.

Before/after evidence is in metrics.json. Fresh-request regression was run red before
implementation:27tools/26495JSONcharacters. It now passes with2tools/2813characters.
All skills enabled expose6tools/14817characters. These are schema-character measures,
not token, latency or semantic-quality benchmarks. Actual PydanticAI FunctionModel
checks skill load -> typed route search -> joint closure on consecutive model steps,
per-run isolation, no duplicate submission for saved results, and strict field handling.
The initial prepare_tools constructor keyword was unsupported by installed2.66.0;
replaced with the current documented PrepareTools capability and rerun successfully.
One local variable reused two unrelated types; renamed, mypy passed. Initial lint
found import order and one unused test import; fixed, no checks disabled.

Checks:323backendunit,45realClickHouseintegration,Ruff,mypy226files pass. Frontend
verify passes36rules/typecheck/Biome/448tests/build. Existing PostCSS/chunk warnings
remain. Global backend formatting debt recorded by the previous task is unchanged;
new request/facade/test files formatted separately. All5skillvalidators andgitdiffcheck
pass. No paid LLM call or new live scenario. Source documents: docs/chat.md and ADR
section in docs/design-decisions.md. No mobile checks or layout redesign.

Local API8007 restarted only after scenario and analysis queues were idle. PID77015,
GRAPH_DIR=data CHAT_ENABLED=true ROAD_WORKERS=6, log/tmp/plexus-unified-tools-api.log.
Frontend remains5187. Existing calculations preserved. Actual live LLM behavior remains
unmeasured; the deterministic model tests verify tool exposure and execution contracts.
