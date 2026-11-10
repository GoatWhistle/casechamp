# SESSION.md detail archive, 2026-11-10

Mutable status paragraphs moved verbatim from `context/SESSION.md` during compaction.
User instructions stayed in SESSION.md.

## Final readiness work resumed

Work resumed on feat/model-validation. Mandatory closeout: work/release-readiness.md. Empty-frequency explanation and version-reset notice added; frontend verify (375 unit tests) and 7 targeted browser scenarios passed. Draft v2 predates these changes. Vasilyevka evidence recorded in work/experiments/vasilevka-coordinate-check.md; raw inputs preserved, coordinate correction and graph/exports rerun remain open. Do not claim final delivery.

## Publication authorized

Branch feat/model-validation; source HEAD c5dc29e before this state commit. Frontend verify passed (375 tests). Push target origin/feat/model-validation. Archives/data remain ignored; coordinate corrections and final delivery remain open.

## Local synchronization, 2026-11-09

Current workspace branch remains feat/transport-graph. origin/main 81b6524 contains the latest frontend; deleted remote feat/frontend is superseded by main. origin/feat/model-validation f666d8e descends from main. Local acquired datasets are preserved by commit 66253c1; live preview integration is preserved by commit 152b06d. Full pre-sync context is archived at work/integration/local-before-sync-20261109/. Data backup and pre-merge hashes: /private/tmp/keys-champ-merge-backup-20261109/. Merged in f8d6078; working tree verified clean.

Local sync verification: all 1664 pre-existing data files (4758822795 bytes) retain their SHA256 hashes. Full frontend verify passed (375 tests and build); backend Ruff/mypy and 138 unit tests passed. Existing indices and pilot exports retained unchanged from model-validation; Stavropol buses remain catalog-only additions to the fixed national calculation. Preview runs from the main workspace at port 5187 (session 8738), API 8000 (session 43661). Model tests: 21 passed. HTTP smoke checks passed for ready indices, Tuva pilot, Crimea geometry, 653 Stavropol links and downloadable bus archive. No push requested.

Prior validation details: [archived history](local-before-sync-20261109/validation-history.md).

## Brief reading, 2026-11-09

User request: «прочти тз хакатона». Read TASK, requirements, QA and both original PDFs under brief/sources/2026-11-09. No implementation changes. Branch feat/transport-graph; HEAD 77436c889e14f11d0ff1e2ee5437e2fe03f5508f. Next: await user direction. Existing dataset changes preserved. Submission timezone/form remain unresolved; saved organizer deadline is 10 Nov 23:39. No product checks needed for reading.

## Data artifacts published, 2026-11-10

Artifacts live in the main checkout data/; worktree map-first-ui now symlinks data -> main checkout. casechamp.duckdb and graph_ru.tar published with SHA-256 as GitHub release data-20261107 (both assets verified uploaded: casechamp.duckdb 1223700480 bytes, graph_ru.tar 639170560 bytes). SHA-256: casechamp.duckdb 98aa172823e882548ac3e465792afffb8fd1ca4c6b600520e83fad70bc458b27, graph_ru.tar cac90fe9b4445696b2b958165cfe575e9888839b026ea3b0f43d90aaefd917cc. Pointer committed in docs/data-pipeline.md (bbfa108) and pushed to goat/feat/map-first-ui. Do not run two writers on the shared DuckDB.

## New-route features implementation detail, 2026-11-10

User: «делай оба» (add-new-route for pilot and for national index recompute).

Backend done, not committed; checks green (171 unit tests, ruff, ruff format, mypy strict).

Feature 1, pilot additions: POST /api/v1/pilots/{id}/evaluate accepts `additions`
(from/to point, mode, travel_h, seasons, frequency_per_week 1..28 for scheduled modes,
bidirectional). Domain `added_edges` in backend/src/app/domain/pilot_routing.py; NewLink in
domain/pilot.py; schemas NewLinkRequest, EvaluationRequest.additions (max 10), echoed in
EvaluationResponse.additions. Tests: tests/unit/domain/test_pilot_additions.py, usecase, HTTP
round trip in test_pilot_routes.py (added air link Kungurtug–Kyzyl 1.2h/14 per week → 7.2h).

Feature 2, national what-if: exact incremental Hansen recompute. New domain module
backend/src/app/domain/market_scenario.py: link weight = travel + 84/frequency + overhead
(air 2.5h, rail 1.0h, road none; unknown frequency assumed 1/week with assumption tag);
Floyd–Warshall relaxation of the 180×180 city matrix, then best(i,j) update only for improved
columns over the 155k-point road_h matrix, Hansen delta per point, population-weighted region
aggregation, normalization to fixed road base ×100. usecase/scenarios.py (ScenarioQueries,
StaleScenarioVersion→409), repository/files/scenario.py (mmap .npy artifacts from SCENARIO_DIR,
default data/scenario_ru; DataUnavailable→503 when absent), controller/scenarios/
(GET /api/v1/scenarios catalog of 180 market cities; POST /api/v1/scenarios/evaluate, 1..5 links,
seasons road/summer/winter). numpy added to backend deps and to PURE_LIBRARIES in
tests/unit/architecture/test_dependency_rule.py. Settings gained scenario_dir (env SCENARIO_DIR).

Stale atlas test expectations updated to the current 12391-link catalog (were 1650; Stavropol
registry asserts now check the source_date 2026-10-20 subset of 653 rows). backend/openapi.json
and frontend/src/shared/api/schema.gen.ts regenerated (API_SCHEMA_URL=../backend/openapi.json
npm run api:types).

Data: local data/casechamp.duckdb (release data-20261107, 1.2 GB) holds the OLD pre-waiting
np_city_times; it does not reproduce published indices.json artifact 7868caee (median region
deviation ~3×). ETL implementation files match the published index manifest hashes, so a rerun
reproduces the v2 model up to graph differences. data/graph_ru/ways.parquet lacked
operating_season; enriched in place (ferry→unknown, is_seasonal→winter, else all) — an
approximation recorded as assumption seasonal_roads_approximated_from_is_seasonal. Background
rebuild running: SCENARIOS=road,summer,winter uv run python etl/access_russia.py, log
/tmp/claude-1000/-home-dev-projects-casechamp--claude-worktrees-map-first-ui/69608258-22f4-4b94-a732-0a97977ec1fd/scratchpad/access_rebuild.log.
After it finishes: uv run python etl/export_scenario_matrices.py (validates city-matrix closure,
reports diff vs published indices.json) → data/scenario_ru artifacts for the backend.

Frontend remaining: pilot-experiment add-route form feeding request.additions;
entities/scenario + features/scenario-lab + pages/scenarios route "/scenarios" + nav item +
scenario.json namespace in resources.ts; then cd frontend && npm run verify. Deadline 10 Nov 23:39.
