# Complete runtime migration

User: move runtime reads to ClickHouse; parse JSON into typed tables; delete migrated source files; tune indexes for actual queries. Local only, preserve unrelated edits/root HTML. No delegation.

1. Capture API/graph baseline before replacement.
2. Materialize typed atlas/settlement/geometry/airport/index tables with source order, region/id sorting and search indexes; retain source evidence in DB.
3. Switch atlas and search/read APIs to typed ClickHouse records.
4. Replace every graph DuckDB query with named parameterized ClickHouse queries; load graph arrays via Arrow once. Version caches by DB snapshot rather than input filenames.
5. Move saved jobs/analysis state to DB; keep only explicitly derived numeric caches on disk.
6. Support scenario matrices from database, preserving current missing-artifact behavior if no source exists.
7. Index/precompute read models for region/season, point/market, way IDs/references and name lookup; EXPLAIN and benchmark.
8. Compare old/new API and numerical baselines, restart with source paths hidden, run tests, then delete only inventoried migrated files. Keep manifests with hashes/counts/provenance in DB/evidence.

Existing local CH: .env.analytics,18123; API8001/UI5187 (other session8003/5189 must also stop reading source before deletion). Source dataset125290049rows/50tables and95atlas docs already copied. User caches/scenario results must not be mistaken for original datasets and silently lost.
