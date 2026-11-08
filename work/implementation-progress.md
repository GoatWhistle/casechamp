# Implementation record

Baseline: main 81b6524f5724032bc707b2433eca6713594607ce. Plan: project-plan.md.

## 2026-11-09: inputs and model

- Existing DB/graph search: `rg --files --hidden --no-ignore` in hackathons, Downloads,
  Desktop, filtered for `.duckdb`, graph nodes/edges Parquet and source archives: none found.
- Restoring settlements/intercity through existing downloader: completed. Remaining BDMO and
  national Geofabrik PBF downloads started; live shell handles recorded in session until complete.
- Root Python 3.14 attempted a DuckDB source build. Stopped it and used installed Python 3.12;
  pinned `.python-version` for the root ETL. `uv sync --python 3.12` succeeds.
- Regression command: `uv run python -m unittest discover -s tests -p test_transport_model.py`.
  Before fix: 2 failures, Palma=1e13 vs .25, waits=[24,24,24] vs [84,42,28].
  After fix and expanded cases: 6 passed. Synthetic controls, no national recalculation claimed.
- New national extraction preserves full OSM tags and classified operating season; graph routing
  filters ways before constructing CSR. Unknown seasonal roads/ferries excluded pending evidence.
- National access calculation retains finite travel times beyond 72h (Harris tail matters),
  road baseline excludes trunk air/rail, replacement tables promoted in one transaction.
- Telegram chat synced through message 270; deadline message 266 preserved in brief/QA.md.
  Timezone and submission form remain unavailable.

Next: finish source restoration and manifests, verify national graph construction and full
calculation, build a versioned Tuva graph, implement pilot API/UI and complete deliverables.
