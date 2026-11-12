# Traffic integration working state

Branch feat/transport-scenarios-update, initial HEAD 986ae0f5ee754b9e98f25e2e608b5bc37cbad507. Many unrelated dirty files owned by another session; preserve all. No commit/push requested this turn.

Implemented: installable etl/pyproject.toml plexus-traffic-model shared by CLI/backend. Split snapshot/candidate file IO and housing extraction from pure runtime. TrafficSource/Store/Port + background jobs; new ClickHouse plexus_state.traffic_jobs schema added in stress.sql and applied locally. National housing inventory accessible through manage_calculation(kind=traffic_data); calculate_scenario(kind=traffic_development) accepts bbox, exact region or explicit pair. Saved IDs via manage status/cancel/recent. New bundled traffic-development skill. Traffic NDJSON event and generated API contract, durable chat entries, polling, auto result commentary, red traffic overlay and vivid green proposed links. No zone points or scope rectangle after explicit user corrections. No permanent deep-link preview: traffic-link.tsx deleted and removed from MapChat; results only belong to requesting agent message. Short table headings, row selection replaces broken four-way project Segmented.

Index now primary: TrafficIndices reuses GraphRouting.calculate_details with WeightedRoads overrides, same 180 markets, 2h half-life, atlas population/normalization. Local congestion times replace matching directed source edges, outside-window weights unchanged; existing index method is representative undirected. Calibration is not reset to 100. Baseline and each converged comparable-demand alternative compute full regional indices for regions in window; primary UI before/after/index delta, hours only backend audit. Pending real end-to-end index validation.

Runtime: primary API8007/UI5187 left alone. Separate UI5190 (Vite, exec15243), API8817 CHAT_ENABLED=true GRAPH_DIR=/private/tmp/plexus-traffic-runtime (latest exec11023), process startup is ~15s. Root .env.analytics for CH credentials, never print. API before current latest had exec16997 and was stopped after checking no active jobs; a user closure-analysis request raced shutdown (ID45d792ef53734501b7eb211d54d513b5). Check its status and resume if interrupted. Do not stop current user work to restart blindly.

Checks so far: backend ruff+mypy passed; 423 unit tests and 49 integration tests passed before latest zero-cost validation fix. Frontend verify passed 486 tests before 5 newly added tests; 3 map tests passed; two index component tests were corrected from unavailable toBeInTheDocument matchers and are rerunning. CLI22 tests pass. New test files tests/unit/adapter/traffic/test_calculation.py and extra weighted-index tests in test_routing.py. Source files <=250 after extracting minimum_csr to weighted.py (routing246, traffic calculation241).

Real pilot legacy traffic run traffic-ade815d40dff490ca102da8685e02715 completed 3 alternatives and preserved geometry, baseline8163.508vehicle-hours/20 overloaded; cap4.33385h saved/18 overload; speed185.52728h/20; new link -0.02718h/20. This old run has no index, must never substitute hours. User saw it through the now-removed preview and rejected the global placement, dots and hours.

Memory failure fixed: housing_current full argMax aggregation exceeded CH2.33GB. Runtime query now filters IDs from raw housing by bbox before canonical view aggregation; same current records, 14106 houses in bbox41.55,43.8,42.25,44.95. Do not add query SETTINGS under readonly=1.

First real index run traffic-cf7287d97dac4144a5de6dc559c1302d failed at WeightedRoads.validate because original full graph contains zero-cost connectors or infinity; validation fixed to permit nonnegative/infinite original costs, reject NaN/negative. Current API must include fix. Launch next real index run after health ready, save result. Files /private/tmp/plexus-traffic-index-job.json and result hold prior failed ID. Backend worker no paid model needed; do not send paid chat test. User did retry closure query in product themselves, that is authorized usage.

Outstanding: real full index run, source/index/repository integration checks, tool contract checks without model, user-visible chat ordering/green new links verification, docs and exact new demo prompt, final full required checks/context budget. Current browser via native CUA Chrome object chrome, no browser providers. CUA state APIs required before actions. Last viewed localhost5190 chat contains user closure question and prior disabled-chat error; chat now enabled. Do not use shell/browser automation instead of CUA for UI. No direct UI state injection or new global preview. Need preserve user final request.

## Final validation

Shared-model full real-data run completed: traffic-3b4f60842c8948ff84c1e3f5254acd4a, 841 OD pairs,
8865.89935 modeled cars/hour, 14105 used residential objects, 157 bound settlements.
Indices use normalization7897244.511692026 and full regional populations. Baseline KChR90.02131618,
Stavropol99.12077776, Krasnodar93.47053270. Speed+20% on «Кавказ» gives deltas+.64703748,
+.04224897,+.01176011. Capacity changes produce zero index delta. New1.799816km hypothetical
link gives+.00324654,+.00137637,-.00000483. All demand comparisons converged, no rerouting
benefit invented. Report docs/results/traffic-agent-validation.json.

Primary API8007 updated from idlePID44106, preserving GRAPH_DIR=repo/data, CHAT_ENABLED=true,
ROAD_WORKERS=6. Latest runningPID92957 exec20977 before final activation. UI5187 unchanged.
Private8817 exec11023 still owns user closure-analysis45d792ef53734501b7eb211d54d513b5, which
was resumed under the same ID after shutdown race. Do not stop private server while active.
Private UI5190 exec15243 remains available; primary is the intended final entry point.

Final checks: 425backendunit,49integration,492frontend,22CLI passed; ruff+mypy+36frontendrules
passed. CLI help initially failed without PYTHONPATH; corrected documented PYTHONPATH=etl
command passed. Docker backend build awaiting final image export; Compose config passed,
buildcontext1.40MB excludes all data/secrets. Frontend existing chunk-size/PostCSS warnings remain.
No paid model was called by validation. A user themselves invoked the closure prompt in the
private product UI. Tool contract tested against real primary API:3regions/3proposals,
compact event22480bytes and reply19326bytes, automatic-review prompt22191bytes.

Late fixes: records retain indices but stream artifacts omit geometry; card fetches geometry
through typed API. History retains traffic IDs and scope. Result stays attached to original
agent message. Proposed link green styling also updates already-existing map layers. Selecting
a proposal focuses its actual road geometry, not the whole window. Small index deltas show
enough decimals to avoid negative zero. Numeric fallback OSM IDs are hidden from road labels.

Final Docker backend build passed (plexus-analytics-backend:latest), shared-model import
inside an isolated network-free container passed. Frontend final lint/build and precision
regression tests passed. MainAPI finally activated current source in exec37828 after an
additional idle-job check; default index routing has its own 4-worker pool. All recorded
primary settings preserved. No deployment, commit, push or paid model check.

## Closeout corrections, 12 November

Completed results now show local mean trip minutes beside the regional index.
The exact user's saved case traffic-faeb74c2918c432e9ca2da334a87942e gives
16.4005492218 before,16.2062126031 after speed improvement on Kalinina street.
Regional changes are below display resolution and shown as unchanged. Negligible
alternatives are omitted from the compact shortlist; original results remain stored.

Pending cards show a brief status without partially filled tables. Default overlays
show only the selected project, red for existing roads and vivid green for cleared
new links. Housing/zone dots and framing boxes are absent. Background graph rendering
cannot cover the selected road highlight. Old unchecked links are excluded. The
reported chord through buildings is rejected by the residential buffer check.
This check uses centroids and area-derived conservative buffers, not full engineering
feasibility. See docs/synthetic-traffic.md.

Chat prose and calculation cards now share body-small typography. Followups appear
before compact “Ход анализа” metadata so metadata does not split the response.
No historical assistant replies were edited. Runtime methodology/provenance stays in
stored records and technical docs; the normal result payload leads with mobility
and the regional index. User-requested explanations may still describe methods.

False closure isolation of Izobilny was reproduced and quarantined at the calculation
layer. Exact cause, fixtures and live checks: ../closure-anchor-diagnosis/README.md.
This is an integrity guard, not a replacement of the national single-point origin model.

Checks: frontend verify passed,498tests,36rules,typecheck,lint,build. Backend full
unit441passed including the final stale-ranking regression. Ruff/mypy passed. Integration49passed with .env.analytics. The first
integration attempt lacked the required environment and failed clearly; rerun passed.
The first narrow mypy invocation from repository root missed backend configuration;
the configured backend run passed. No paid model evaluation. Both APIs were restarted
idle and live checks confirm the false closure is rejected on8007and8817 and local
trip metrics are present. Browser reading confirmed compact typography/actions in
current user chat; no paid prompts were sent. No mobile checks.

Publication: implementation afd1d975c1e21caa1720ea3ca5d0dfff71ac24c3 pushed to
origin/feat/transport-scenarios-update, remote SHA matched. Working tree was clean.
CLI22tests passed using the backend environment with PYTHONPATH=etl; root .venv
does not include pytest. No ignored source datasets or credentials were staged.
