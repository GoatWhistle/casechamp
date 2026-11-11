# Server-side corridor speed edits, 2026-11-11

Branch feat/map-first-ui, base cdb2c2e1108bde7ff37ab91f9d7907d05de2a897.

The road resolver intentionally omitted way IDs, but calculate_scenario previously
accepted corridor IDs only for closures. Explicit network edits required all IDs
and had a 50-way limit. Added edit_selection to the existing scenario tool with
selection_ids and speed_factor. The resolver expands and deduplicates selections
internally and queues the joint changes for endpoint/crossed atlas regions using
the existing RoadJobs engine. No prior closure is inherited. One combined card
carries geometry and jobs to the UI; model output contains counts/status/IDs only.

Status/history now limit changes to 20 and status settlement effects to 10, marking
truncation and preserving full saved jobs. Agent skill and capabilities explain
selection edits and their open-network baseline. This calculates regional indices;
it does not add pairwise trip-time comparison or traffic forecasting.

Regression: new schema/dispatch test failed before implementation; passes with
5000 unique ways across two overlapping selections, two region jobs, one card,
compact reply, and exact factor1.2. Invalid selection/factor cases never submit.
Status/history test confirms full jobs remain intact. No paid model call.

Checks: Ruff and mypy passed; 397 unit tests passed before adding the seventh
focused regression (all7 focused tests passed afterward). Initial integration
invocation failed because ClickHouse env was not loaded; rerun with .env.analytics passed all48integration tests.
Local API8007 PID34705 had8active scenarios at first restart check and4at final
check. It was NOT restarted to avoid cancelling those calculations. Next: restart
the main API once current jobs finish, preserving .env.analytics, GRAPH_DIR=data,
ROAD_WORKERS6 and CHAT_ENABLEDtrue. Tool changes require that restart.

Context budget passes with protected-instruction notice. Later verbatim blockquotes
were grouped under Explicit user instructions, no instructions deleted. Prior full
session retained in session-before-compaction.md. No frontend change or paid model run.
