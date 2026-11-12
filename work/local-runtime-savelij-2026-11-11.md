# Local map-first runtime, 2026-11-11

User corrected the launch branch to feat/map-first-ui. Fetched origin, switched from main
to origin/feat/map-first-ui, HEAD 0c7cb89. No product source changes or commits/push.
The only prior tracked edit was this session's main launch note, backed up at
/tmp/casechamp-session-before-map-ui.md before switching.

Docker Desktop started. Created ignored .env.analytics with a random local DB password.
ClickHouse runs through compose.analytics.yaml, project casechamp, port18123.
Downloaded release data-clickhouse-20261110 into ignored .local/snapshot. Restored
plexus_atlas, plexus_accessibility, plexus_casechamp, plexus_graph and empty
plexus_scenario; SHA-256 and every restored row count verified by restore_snapshot.py.
Created plexus_state schema. Staging refresh graph and archive-only additional tables
were not restored. Matrix:83845118 rows; graph:17393384 edges,6990556 nodes.

Backend dependencies installed with uv sync --python 3.12 --no-dev. Initial default
3.14t sync tried building dev DuckDB and was interrupted; 3.12 runtime install passed.
Backend launched using backend/.venv/bin/uvicorn app.main:create_app --factory
--host127.0.0.1 --port8000, with .env.analytics exported, CHAT_ENABLED=true and
GRAPH_DIR pointing to .local/runtime-cache. Vite8080 proxies to8000.
An initial temporary API without GRAPH_DIR was replaced by this full graph runtime.

HTTP checks passed for health, overview,82regions,index,sources,road-scenarios,
location search and road graph viewport38,54,43,57 zoom7 (29765 segments).
Desktop Chromium1440x1000 showed the latest map/chat without JS errors. Initial
networkidle wait timed out; DOM-content-loaded browser check passed. A first road
check during API restart returned502, retry after startup passed. Wrong location
query parameter q returned400; documented query parameter returned real places.
No tests, mobile checks or model prompts sent. Chat is enabled but live auth/stream
not tested. Separate /scenarios matrices remain empty in the published snapshot.
Next: user review on http://127.0.0.1:8080.
