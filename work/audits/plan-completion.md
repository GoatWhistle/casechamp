# Completion audit against work/project-plan.md

2026-11-09. Previous goal turn: progress (implemented, verified and packaged local stages).
This continuation independently checked the plan, source tree, artifacts and external chat.
The full goal is not complete: stage7 requires a form and an actual receipt.

## Evidence boundaries

- Source release submission-1 is4b37636534a46b51742082f7ab6750b340fbced1.
- Runtime files backend/, frontend/ and compose.yaml have no diff since the clean-checkout
  verification at9a1ad84. Later changes are documentation, tooling and internal records.
- Clean and scrubbed Compose runs and4 browser cases are recorded in
  docs/results/stand-validation.json; prior tool outputs show all4 pass in both directories.
- Hash verification of pilot/national report implementations covers11 current files.
- This audit found the pilot validator wrote data/pilot-validation.json while the published
  docs report remained older. Added --output, made the shipped report the default output,
  explicitly separated candidate output in the pipeline instructions, reran24 comparisons and
  the200-sample benchmark. Numerical results, pilot version and application runtime are unchanged.
- Source transport operability is not proved by algorithm tests; it remains a stated limit.

## Stage1: inputs and reproducibility

| Requirement | Evidence | Verdict |
| --- | --- | --- |
| Preserve audit, state and R01–R18 map | work/audits/project-alignment; context; docs/requirements-map.md | local complete |
| Find snapshot or restore missing inputs | initial audit and restoration progress; data/source-manifest.json | restored, original database absent in inspected locations |
| Sources, dates, licences, hashes, code, parameters, exclusions | docs/results/source-manifest.json, national-graph-manifest.json, national-manifest.json; pilot-sources.md | recorded; publication URLs are not current-service validation |
| Separate download/graph/calculation/export and reuse inputs | etl/download.py, graph_russia.py, access_russia.py, indices.py, export_indices.py | implemented and executed |
| Check pilot links with periods and assumptions | pilots/tuva.json, docs/results/tuva-provenance.json, pilot-road-tag-audit.json | historical source/model check complete |
| Missing input fails clearly | repository/controller unit checks; clean error recovery e2e | verified within declared scope |

## Stage2: model invariants

| Requirement | Evidence | Verdict |
| --- | --- | --- |
| Preserve edge season/provenance; filter closed edges first | seasonality.py, graphlib.py; test_closed_edges_are_removed_before_route_search | checked |
| Separate transport mode from season | five national scenarios; API network_mode and season; national-index e2e | checked |
| Shared84/f waiting, no24h cap | waiting.py, access_network.py, manual_links.py; frequency controls | checked under uniform-headway assumption |
| Irregular Tue/Thu49.714 vs uniform42 sensitivity | test_irregular_schedule_wait_is_a_separate_control; pilot-method.md | checked; not substituted into scenario delta |
| Independent transfer waits and same baseline/variant model | pilot_routing.py; disclosed in UI, JSON, method | implemented and disclosed |
| Travel/wait split and optimistic no-wait bound | TripResult, evaluation output; domain and HTTP checks | checked |
| Unknown frequencies and assumptions retained | test_unknown_frequency_is_preserved_and_assumption_marked; pilot tests and exported inputs | checked |
| Fractional Palma, missing/zero/normalization | test_palma_splits_settlement_population_at_quantiles, test_palma_handles_missing_zero_and_invalid_weights | checked |
|72h cutoff evaluated separately | cutoff-sensitivity.json | measured, finite tail retained |
| Seasonal graph before shortest-path compression; removal preserved | test_compressed_seasonal_graph_matches_original_with_link_removal; provenance | checked on small source/squeezed graph cases, not exhaustive PBF equivalence |
| Known path distinguished from proven optimum | test_known_route_reports_incomplete_unknown_alternatives | checked |
| Explicit centres; no medical/interseason claim | pilot pairs, passport, limitations, UI warning | inspected |

## Stage3: national layer and pilot

| Requirement | Evidence | Verdict |
| --- | --- | --- |
| Hansen1/2/4, common base and valid regional IDs/weights | national-validation.json;410 region rows,777060 point rows, road mean100 | checked |
| Versioned export, manifest and visible coverage |7868caee… artifact; national-index e2e; map/table API fields | checked |
| Additional indices stay supplementary | indices.md; main map Hansen choice | inspected |
| Three named pairs, same-centre comparison and separate local pair | pilots/tuva.json, pilot-method.md, UI result grouping | checked |
| Frequency2→4,2→7 and seasonal closure | pilot-scenarios.csv and24 algorithm comparisons | checked; zero effect retained |
| No cost/investment optimum fabricated | passport, evidence, limitations and slides | inspected |

## Stages4–5: API and UI

| Requirement | Evidence | Verdict |
| --- | --- | --- |
| FastAPI layers, versioned file graph, no national mutation | repository/files/pilots.py, usecase/pilots.py, domain/pilot_routing.py; unchanged-input check | checked |
| Three pilot endpoints and full metadata | controller/pilots/router.py, OpenAPI and real HTTP tests | checked |
| Summer/winter, enable/disable,1–28 integer and reset | domain/controller tests; pilot e2e | checked |
| Original out-of-range frequency retained and editing disabled | test_out_of_range_source_frequency_is_preserved_and_noneditable | checked |
| Found/no_route/insufficient data, invalid/stale/missing versions | domain/controller/repository tests and warning display | checked |
| p95≤2 seconds on fixed machine |200 sequential HTTP requests, Apple M4 Pro, p95~0.001556s | measured locally; no concurrency/remote claim |
| Hansen in map/comparison, mode/season separate | map/table code; national-index e2e | checked |
| Baseline/change, route, split, assumptions and stale result | pilot-experiment e2e and rendered screenshot | checked |
| Loading/errors/incomplete/no_route | page query states,503 recovery e2e, domain/API no_route/incomplete tests | checked at respective layers |
| CSV, JSON and reset, generated API types | pilot e2e; schema.gen.ts vs OpenAPI | checked |
| One actual frontend; remaining exporters documented | docs/data-pipeline.md, running.md; Compose builds frontend/ | checked |

## Stage6: checks and launch

| Requirement | Evidence | Verdict |
| --- | --- | --- |
| Season/monotonicity/unknown-vs-zero/reproducibility |21 root controls, pilot domain tests, full national monotonicity check | checked |
| Small graph manual and independent path enumeration | test_optimum_matches_independent_simple_path_enumeration;24 Floyd comparisons | checked |
| Wait/half-life/target sensitivity | pilot-method and three sensitivity JSON reports | measured within stated scopes |
| Real exports, versions and input immutability |6 integration checks, controller/repository tests | checked |
| Map→pilot→frequency→compare→export→reset | real API e2e on clean and scrubbed Compose | checked |
| Desktop keyboard/long names/errors | national keyboard combobox, longest-name/no-external-load case,503 recovery | checked; no mobile per instruction |
| Frontend verify and backend Ruff/mypy/unit/integration |375 frontend,143 backend; stand protocol and prior outputs | passed |
| Compose health/DATA_DIR, prepared data, clean checkout, no paid keys | fresh clone and scrubbed clone builds, mounted exports,4 e2e cases | passed |
| Compact synthetic controls separate from real data | tests/test_access_network.py, test_transport_model.py, backend domain tests | present and executed |
| SHA, versions, protocol; publication only after success | source tag/manifests/protocol; final exports after validation | checked |

## Stage7: materials and external submission

| Requirement | Evidence | Verdict |
| --- | --- | --- |
| Passport1–2 pages,7 slides and speech≤5min | PDF page counts2/7/2;561 words, estimated269.28s; all rendered pages viewed | prepared; estimate is not live rehearsal |
| Variant table with units and inputs | pilot-scenarios.csv, protocol, passport table | prepared |
| Method/run/requirements/jury route | docs/indices, pilot-method, running, requirements-map, for-jury | prepared, links checked |
| AI task/tool/material/check/error and surviving research | ai-register.md, passport, slide6, appendices; scrub archive inspected | prepared and retained |
| Roadmap: schedules/costs/territories/external validation | slide7, passport, speech | prepared; future work is not asserted complete |
| Primary deadline, timezone and form | brief/QA.md message266; full sync through270 at06:22UTC | deadline10Nov23:39; timezone/form unavailable |
| Compare completed kit with actual form | no actual form obtained | blocked externally |
| Actual receipt; no unauthorized message/submission | no receipt; no message/submission performed | not complete |
| R15 historical timing | no genuine early passport receipt located | unconfirmed, cannot repair retroactively |

## Next action

Corrected release2 is prepared: source4915346, cleaned d1af715,11 implementation hashes verified.
Retain the whole goal. Further stage7 work requires
an organizer form (and its actual fields), timezone evidence and explicit authorization for team
submission. Do not repeatedly rerun already-passing application checks while these facts are absent.


## Blocked audit, 06:27 UTC

Previous continuation was progress: repaired published report, independently checked11 hashes,
completed this requirement audit and prepared release2. Current turn revalidated unchanged source
and full chat history. The same external blocker is present in three consecutive goal turns:
06:18,06:22 and06:27UTC full syncs all end at message270, without a submission form.
No local implementation or artifact work remains after the audit. This is an external impasse,
not evidence that the full goal is complete. Set goal blocked until a form/fields and the user's
submission instruction allow stage7 to proceed. Release tag/archive remain unchanged by this
internal audit record. No messages or submissions were sent.
