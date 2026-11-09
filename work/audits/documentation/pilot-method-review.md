# Audit of docs/pilot-method.md

Scope: exactly `docs/pilot-method.md`, checked in detached worktree at
`a9c44a1dec8db814625d6ba0986b222f2207b380`. Read-only inspection of related code,
artifact and reports. Parent subsequently copied the new compression control into
`tests/test_transport_model.py`; this report distinguishes that uncommitted addition.
No product document edited, no missing-input ETL, paid call, browser/mobile check,
commit or push performed.

## Findings requiring clarification

1. **Reproduction command has an unstated input dependency (lines 72–76).**
   `etl/validate_pilot.py` defaults to `data/pilot_candidate`, absent in this worktree.
   The shipped artifact is instead `frontend/atlas/public/pilots/tuva.json`.
   Recommend `PYTHONPATH=backend/src uv run python etl/validate_pilot.py --data-dir
   frontend/atlas/public`, and disclose that the script writes
   `data/pilot-validation.json`. The displayed command is valid only after producing
   the candidate directory; it is not a self-contained check of the committed artifact.
   I did not run the script's writing entry point. I imported its independent method
   and exercised the committed graph entirely in memory.

2. **Access-tag result is unverified, not shown false (lines 61–62).**
   `docs/results/tuva-provenance.json` contains exactly 133 unique OSM way IDs,
   verified by collecting `roads[*].osm_way_ids`. It contains no tag values or
   access-audit result. `etl/pilot_export.py` also does not perform the claimed
   access-tag audit. The raw PBF is absent here. The claimed absence of four
   restriction tags may be true, but it cannot be established from committed
   evidence. Add a reproducible tag-check command and saved result with PBF hash,
   or label this specifically as a manual check with evidence, or omit the negative
   restriction claim. Do not treat an ID manifest as proof of access permissions.

3. **Make the scope of 24 comparisons explicit (lines 66–67).**
   This number is correct: 2 seasons × 4 variants (baseline, frequency 4,
   frequency 7, simultaneous disabling of manual:5 and manual:6) × 3 pairs.
   `etl/validate_pilot.py:55–72` independently constructs a matrix and compares
   production `changed.total_h` with SciPy Floyd–Warshall, including no-route
   outcomes. It does not independently validate source truth, road extraction,
   warnings, route edge IDs, optimistic results, waiting sensitivity or all request
   inputs. All 24 comparisons reuse one graph and the same model assumptions;
   these are not 24 independent empirical observations. Suggested wording:
   “24 сравнения времени: 2 сезона × 4 варианта × 3 пары; независимая реализация
   кратчайшего пути на том же артефакте”. Existing wording is not numerically false.

4. **Specify synthetic compression-control scope (lines 68–69).**
   At committed HEAD the claimed original/compressed equivalence test did not exist.
   Parent supplied its pending addition,
   `test_compressed_seasonal_graph_matches_original_with_link_removal`
   (`tests/test_transport_model.py:81–105`). It passes and compares all node pairs
   on a seven-node, three-way synthetic network before/after omitting one way.
   Retain the claim only with this addition and describe “синтетические контрольные
   примеры”. It establishes a control case, not original-PBF/national-graph equivalence.

## Facts verified and wording that can remain

- All displayed times and deltas match fresh in-memory evaluation of the committed
  artifact: 18.0951086803 h baseline/4, 14.2433304669 h at 7, delta
  −3.8517782134 h; Toora 4.5053524266 h; Systyg summer 88.4 h/winter 2.6 h;
  seasonal closure gives no route in both seasons.
- `84/f` follows a 168-hour weekly period with uniform headways and uniformly
  random need. `(48² + 120²)/(2×168)` is 49.7142857143 h; uniform 2/week
  gives 42 h. The page correctly treats this as a separate sensitivity, not a
  full itinerary schedule computation.
- The unknown-frequency warning mechanism is correctly described.
  `unknown_alternatives` gives all source-unknown scheduled edges zero waiting,
  including edges with an assumed calculation frequency. This is a lower bound,
  not evidence that an actual faster service exists. Toora warns; Systyg summer
  also warns because its 1/week is assumed. Keep the summer assumption explicit.
- No normalization is required to compare hours for the named, matching trips;
  the page properly separates Systyg's different destination. There is no regional
  scalar/ranking, population aggregation or causal investment-efficiency claim here.
- Seven points, 19 edges, three pairs and artifact version agree. The report's
  artifact byte SHA matches the committed JSON; the displayed artifact version is
  the normalized-payload SHA excluding `artifact_version`, as enforced in
  `backend/src/app/repository/files/pilots.py:114–120`. These are deliberately
  different hashes. Calling the displayed value “версия артефакта” would improve clarity.
- All six implementation-file hashes in `pilot-validation.json` match current
  files at audit time. Historical dirty=true does not invalidate those file hashes.
- Geofabrik provenance lists the road paths; missing raw inputs prevent independent
  re-extraction of the graph, snap check and current real-world operability.
- The HTTP report explicitly states 200 sequential loopback requests after warmup;
  the page preserves that scope. I did not rerun HTTP timing.
- API limits, version conflict and error mapping are supported by schemas,
  controller/repository code. Export code includes graph/result JSON and CSV
  units via Russian headers, versions, conditions and last executed changes.
- Backend real-artifact HTTP tests and desktop Playwright scenario exist and cover
  the actions named. Their existence was checked; this audit did not rerun either suite.

## Seven-check outcome

| Check | Outcome |
| --- | --- |
| Needed | Keep: answers pilot comparability, mathematics and reproduction questions. |
| True now | Arithmetic and model verified; provenance restriction claim unverified; command and validation scope need the clarifications above. |
| Process story | No prohibited development narrative found; measurement date belongs to the result. |
| Links | `node skills/docs-writing/check-links.mjs docs/pilot-method.md` returned no output and exit 0; no external URL in this page needs HEAD checking. |
| Water | Concise; limitations affect interpretation and earn their place. |
| Tables | Four columns; homogeneous experiment rows; no oversized prose cell. |
| Form | Title, blockquote, related/read line, separators, claim/question headings and footer present. No diagram necessary. |

## Executed verification

- In-memory import of `independent_times`, `PilotQueries` and `JsonPilotRepository`
  using the existing root Python environment with bytecode disabled: **24/24
  time/status comparisons passed**, repeated evaluations identical.
- Pending compression test alone with bytecode disabled: **1 passed**.
- Link checker: **passed**.
- SHA/count inspection using Python standard library: **passed** as described above.

No full root/backend test suite, original-data reconstruction, source-access tag
check, browser check or current real-world transport validation was performed.
