# Index explanation and completed session notes

## Full runtime database migration, 2026-11-10

Implemented on feat/map-first-ui HEADc82ab1e, local only. Atlas/search/graph/matrices/history
now use ClickHouse; no runtime file fallback. Source files deleted after hash/count checks,
full node/edge equality, API comparison and identical repeat calculation. Derived caches kept.
Details, failed checks and exact source inventory: work/clickhouse-migration/README.md.
API8001/UI5187; restart API with .env.analytics and GRAPH_DIR=data. Preserve concurrent
frontend/chat/airport edits. Separate /scenarios lab still lacks its independent matrices
and honestly returns503. No paid checks, commit, push or mobile checks.
Checks: Ruff/full mypy;157backend unit+40integration;393frontendtests/build; clean backend
container loaded real DB without DuckDB installed. Source deletion inventory124files/2.37GB.
Context budget exception is protected user quotations; preserve them verbatim.


Runtime status check, 2026-11-10 22:11MSK: R-217 closure190ways is active. Krasnodar
job3377918591c4400cbe4471ffa0604ce0 progressed beyond screenshot184/360 to196/360; Stavropol
01f0deb0ffbd4a28af9fc60af68e2046 queued0/360. No reported job errors; healthOK.
API process14632 CPU82.7%, host load52.17; first status request timed out15s, next succeeded.
No restart/cancel/model call or source changes.


Index explanation, 2026-11-10: user asked how the index is calculated and what enters it.
Checked docs/indices.md, docs/limitations.md, etl/indices.py and runtime delta formula.
Hansen uses180population-weighted markets,2hhalf-life, population-weighted regional mean
and fixed road baseline100. Missing graph edges may depress results; no measured GDP/flows.
Branch feat/map-first-ui HEADc82ab1e; no model changes. Existing road refresh remains pending.

Transport contribution follow-up: checked access_network.py/manual_links.py/graph_russia.py.
Trunk rail/air currently assume1departure/week,84hwaiting plus1h/2.5hoverhead, strongly
suppressing Hansen contribution. Manual crossings and OSM ferries use different weights.
New timetable/map records do not establish inclusion in published indices; separate modal
effects require controlled reruns. No code change; branch/SHA and road-refresh next steps unchanged.


User asked for repair ideas: proposed separating planned-trip potential from schedule-aware
accessibility, preserving unknown frequencies, aligning ferry weights and auditing modal
removal effects. Recommendation only; no model change authorized or made.
