# Graph release restoration, 2026-11-10

User: «запуль сюда данные графа из гита посмтоир сам где валяется».
Fetched origin without merging or resetting local edits. Remote feat/map-first-ui advanced63fb9cb→bbfa108;
only upstream code-tree change is docs/data-pipeline.md release pointer, copied into local documentation.
Found GitHub release data-20261107, published2026-11-10, rather than Git/LFS data blobs.
https://github.com/GoatWhistle/casechamp/releases/tag/data-20261107

Installed:
- data/casechamp.duckdb:1223700480 bytes, SHA25698aa172823e882548ac3e465792afffb8fd1ca4c6b600520e83fad70bc458b27.
- data/graph_ru/:6990556 nodes,17393384 directed edges,4301210 ways,155747 point records.
- Downloaded graph_ru.tar:639170560 bytes, SHA256cac90fe9b4445696b2b958165cfe575e9888839b026ea3b0f43d90aaefd917cc.

Both release hashes matched. Archive paths and member types validated before extraction. No previous
DB/graph existed; no files overwritten. DB opened read-only. All17393384 edges checked in Arrow batches:
zero out-of-range endpoints/way references, zero negative/nonfinite times. All180 market nodes valid.
DB np_city_times83845118 rows. Verification JSONs under data/releases/data-20261107/:
graph-verification.json, database-verification.json, consistency-check.json. Data remains gitignored.

Compatibility finding: release description claims5 scenarios, actual DB has road/summer/winter only,
84 regions and252 regional rows. Current UI export has82 regions/5 scenarios/410 rows.
index_model_metadata and market_city_legs are absent. ways.parquet lacks operating_season.
All4 graph file hashes differ from docs/results/national-graph-manifest.json. Released road index
for Volgograd is93.79380259017849; current road/road_summer index is61.55079117766899.
Do not mix cached UI baseline with scenario results on this snapshot. Current API exports unchanged.

Next for original recalculation request: reconcile snapshot/model (derive seasonal fields and rebuild
baseline with fixed current methodology, or obtain the matching newer artifact), then wire a versioned
scenario worker. National road-edge tool is still not connected; availability blocker is now compatibility,
not missing files. No database migration, national recomputation, application tests, commit or push in
this download step. Data validation above is what actually ran.
