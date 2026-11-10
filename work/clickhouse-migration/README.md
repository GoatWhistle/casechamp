# Runtime migration, 2026-11-10

Branch feat/map-first-ui, HEAD c82ab1e. Local only; no commit/push/deploy. Preserve concurrent airport/chat/frontend work. Main API8001, UI5187. Old API8003 was already stopped. Source environment from .env.analytics before starting API; GRAPH_DIR is now derived cache root.

Completed:
- 50 imported source tables /125290049 rows retained; 95 original atlas documents archived in ClickHouse with SHA256.
- Typed atlas tables, search normalization and ngram index, regional matrix pruning, OSM ID/reference projections, reference/region/location read models.
- Main composition has no file repositories. Graph uses named GraphSnapshot reads and Arrow arrays. Source equality: all6990556nodes/17393384edges, including duplicates and weights, and454680regional matrix rows with47733infinities.
- Nested state is typed Array/Tuple, inserted through Arrow. JSON writer exhibited1ULP differences and was replaced; float DTO decoding is necessary for stable geometry fingerprints. Five saved analyses compatible; last analysis94a058ce9c3a48fa85e251079275e2db reached paused/batch_complete with10verified results before migration. No active calculation was interrupted.
- Runtime source paths were hidden; API restarted and passed exact response comparison and repeated an existing addition. Numerical result, money and all settlement effects exactly equal; cached calculation0.041935s. Original and new airport matching code differed due to concurrent work; same-code file/DB comparison matched285airports/195assignments.
- Deleted124verified files/2366682834bytes. Inventory: removed-sources.json and DB plexus_atlas.migrated_sources. No remaining source-hold files. Raw external archives/documents and derived numeric caches intentionally retained. Full source materials not all converted to structured records.
- DuckDB moved to dev group; API runtime dependencies exclude it. Old file adapters remain for explicit ETL/test fixtures only. Separate scenario lab had no originaldata/scenario_ru; database catalog empty, existing503behavior preserved.
- Unit tests moved where necessary: acceptance tests requiring imported data are integration tests. Synthetic controller/algorithm tests stay offline. Integration fixtures can reconstruct archived source documents in pytest temp dirs for import validation, not runtime fallback.

Checks/evidence: unit.log, integration.log, frontend.log, api-comparison.json, live-verification.json, graph-comparison.json, index-benchmark.json, schema SQL and source manifest. Failed checks were fixed: nullable bloom expression, JSON float roundtrip, scalar float retyping for fingerprints, Array(String) literals, all610search normalization mismatches. Initial graph comparison failed only because equal(sort-key) duplicate edges had different order; full multiset sort proved equality.

Compose project matches existing plexus-analytics to retain its ClickHouse volume. Cache is a separate named volume owned by app UID; host cache permissions are not assumed. First empty-cache Compose startup builds CSR.

Documentation skill references a nonexistent presentation npm run readme script; diagram colors instead taken from actual frontend palette tokens. No presentation edits, no mobile checks, no paid calls.

Final verification: backend Ruff/full mypy passed;157unit+40integration tests passed after source deletion; focused final storage9passed. Frontendverify393tests/build passed (existing large chunk warning). Docker backend image built; one-off runtime with empty owned cache volume loaded82regions/46487links and graph; asserted duckdb module absent. API8001 restarted with final code and original derived cache. Temporary8002/8004 APIs stopped. No original dataset JSON/Parquet/DuckDB remains at runtime source paths. Stored calculation f8f9b55687844896b09bca7196a74cef is the verification repeat of2f580745b0f948599fc4a712a7f06253.
