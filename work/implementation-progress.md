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

## 2026-11-09: verified Tuva pilot and restored national inputs

- Goal resumed after plan revision and later interruption. User authorized blank team/name/contact
  fields for the passport: «пока что забей, поставь пропуски». Do not ask again for these fields.
- HEAD before current work: cf78089. All 10 PBFs and extracted Parquets restored; all PBF headers
  show source timestamp 2026-11-07T21:21:36Z. Seven tabular snapshots recorded with hashes;
  complete BDMO load has 2,336 municipal rows and 82 regional rows.
- Tuva: versioned 7-point/19-edge artifact; three centre trips; 24 comparisons match independent
  Floyd-Warshall. Known irregular schedule checked separately. Frequency 4 has zero effect;
  frequency 7 reduces Kungurtug–Kyzyl from 18.095 to 14.243 model hours. Local seasonal closure
  leaves Systyg-Khem without a path in this network. 133 selected OSM ways have no explicit
  no/private access tags; operability is still unverified. docs/pilot-method.md and docs/results/.
- Pilot API and UI implemented. Frontend verify passed (375 tests, 36 rules); desktop Playwright
  map → pilot → edit → evaluate → export → reset + axe passed on dev 8080 and Compose 8081.
  Impeccable detector returned []. No mobile checks. Backend unit/integration checks tracked in
  tool output; new repository invalid-artifact tests added. OpenAPI and frontend types generated.
- Docker Compose on port 8081: both services healthy; app runs without paid keys. Dev servers
  remain on 8000/8080. No messages sent or submission performed.
- National graph built: 6,991,438 nodes, 17,395,685 edges, 155,747 points in 84 source regions,
  population 128,796,185; 155,264 road anchors cover population 128,733,761. Manifest data/graph_ru/.
  Moscow (293 points) and Sevastopol (42) are partial source territories; omit them from the
  comparable 82-region index, which has 155,412 points. Do not claim full national population coverage.
- Live national access job: exec session 39747, started before adding separate road_summer/
  road_winter modes. Revalidate handle before acting. road finished with 26,347,467 finite OD rows;
  summer running at last observation. It writes one transaction for road/summer/winter. After it
  completes, run APPEND_SCENARIOS=1 SCENARIOS=summer,road_summer,road_winter: new code excludes
  winter roads/ice crossings in summer and adds explicit car-only seasonal calculations. Never
  launch concurrent DuckDB writers. Regional indices/export still pending.
- New access_network.py prevents remote markets getting free nearest-road links and preserves
  unknown trunk frequency with explicit assumption 1/week (84h wait). Root controls: 20 passed.
- Still required: national indices with common base and sensitivity, API/UI coverage and separate
  season/mode, clean checkout test, documentation/requirements map, passport/deck/speech/AI registry,
  submission-form/deadline recheck and authorized submission confirmation.


## Final local delivery, 2026-11-09

- National rerun73781 completed all5 scenarios and aggregation. Independent formula check initially
  failed at relative1.5e-7 because DuckDB evaluated FLOAT arithmetic. Changed Hansen/Harris
  contribution math to explicit DOUBLE, reran aggregation/export/validation/sensitivity (no graph
  rerun). Final artifact7868caeee9741f577f6281bd55bb4748370dc45203d08dc8da06266882f34f3f.
- Full national777060 origin rows,410 regional rows, road mean100.0, no monotonicity violations;
  12 independent formula samples passed. Sensitivities1/2/4h,72h and largest-target removal saved.
  Removing Moscow costs Moscow oblast66.6% in road_summer; published as a limitation.
- Backend143 combined tests, Ruff/mypy61 sources passed. Frontend375/45 test files,36 guards,
  build passed. Root21 controls and cleanup11 passed. Meaningful frontend change after first run
  formatted the selected-region link and retained network_mode in navigation.
- Four Playwright scenarios passed at8082 from fresh clone9a1ad84 and8083 from scrubbed commit
  53d23629c3d03fbc4eb3808ede1f395949184492. External browser requests blocked; no live network
  disconnect. Error recovery injects503 in test only then retries the real API. No mobile testing.
- Fresh clone /tmp/plexus-clean.iy7oqL built without.env. Scrubbed runtime clone
  /tmp/plexus-submission-check is healthy. Full source history backup/export verified, original main
  untouched. First scrub export failed on legitimate historical SDK references; policy now allows
  product dependency names in exact paths, still rejects generated-by attribution. Next failed on
  obsolete instruction/hook paths in historical design docs; narrow source normalizations fixed it.
- 7 slide PNGs and all passport/speech PDF pages viewed; no clipping. Passport2 pages, deck7,
  speech2. Word estimate561/269.28s is not a live rehearsal. Render list handling fixed in speech PDF.
- Links README/docs/datasets pass. Missing archived raw/derived files are named, not broken links.
  Public AI research copies and AI disclosure survive scrub. Known-token/private-key scan over
  tracked text and all history patches found no matches; this is a pattern scan, not universal proof.
- Chat resynced through270 at06:18UTC, form still absent. Identity blanks intentional. No submission,
  organizer messages, public deployment, history rewrite of source, force-push or paid calls.
