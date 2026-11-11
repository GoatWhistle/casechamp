# Selected-settlement connectivity

2026-11-11, branch feat/map-first-ui, HEAD cdb2c2e1108bde7ff37ab91f9d7907d05de2a897.
User approved a prompt-driven index for arbitrary settlement groups and added:
«да, плюс в случае закрытия тоже пусть умеет оценивать».

Implemented through calculate_scenario(kind=connectivity), with a runtime
settlement-connectivity skill and the existing six-interface tool surface.
2-12 names; all_pairs or to_center; optional jointly closed resolved selections.
The domain fixes the score at 100*2^(-hours/2), with equal pair weights and no self-pairs.
Unreachable pairs score zero and stay in the denominator; unbound pairs make the
aggregate unavailable. Closed OSM ways are removed in both directions; other roads
remain available. Baseline roads only, with no seasonal additions or rail/air.
Source graph data is never changed. Reuses snapshot name resolution and road weights.

Two existing chat table events carry summary and per-pair results. Russian captions,
nulls, road statuses, horizontal scrolling and archive validation are implemented.
Model provenance is not rendered as a broken HTTP source link. Tables remain readable
in the floating and expanded chat. No new animation or mobile validation.

## Verification

- Backend Ruff passed; mypy passed (248 source files at final run).
- Full unit suite: 358 passed before adding the final agent-protocol regression.
  Afterwards 15 focused corridor/group tests passed, including that regression.
- Full ClickHouse integration suite: 46 passed.
- Full frontend verify passed twice after fixes: latest log in frontend-verify.log.
  459 tests, all 36 rules, typecheck, lint and production build passed.
- Graph, usecase and tool tests exercise 2/3/4 points, center mode, detours, parallel
  edges, compound closures, isolation, missing attachment, ambiguous names and aliases.
- FunctionModel test follows load_skill and the actual typed calculate_scenario
  protocol with an independently routed fixture; no paid LLM call.
- Real data: validate.py uses local ClickHouse, then saves baseline.json, closure.json
  and the emitted events.json. Group: Stavropol, Aleksandrovskoye, Svetlograd,
  Blagodarny, all Stavropol Krai. Six pairs. Graph road-8033092fca2cf5fa.
  Baseline 58.22761512798345, closure 25.247349109261307, delta -32.98026601872214,
  three newly unreachable pairs after closing all 70 ways of the fastest baseline
  Stavropol–Aleksandrovskoye route. This is a whole-route closure, not one bridge.
  Independent SciPy validation: three baseline pairs and all six closure pairs match.
  First observed closure run 33.285s; final run 8.890s, warm baseline 0.305s.
  Timings describe these local runs only, not a performance guarantee.
- browser.mjs replays actual computed table events through the chat stream on localhost5187.
  Desktop1440, normal/expanded window, horizontal scrolling and history reload passed.
  Table viewport374px/content1387px, row45.297px; zero page errors and zero axe violations.
  Screenshots: desktop-1440.png, expanded-1440.png, history-1440.png.
- git diff --check passed. No commit/push/remote deployment.

## Checks that initially failed and limitations

Initial unit collection collided on two same-named test modules; the adapter test was
renamed test_group_connectivity.py. A disallowed em dash in new UI copy was removed.
Browser text selector matched both heading and caption; it now selects the heading.
The first image exposed per-letter table wrapping; scoped horizontal layout fixed it.
Axe requires an explicit browser context; the runner now creates one.

Global Ruff formatting remains unclean (74 files flagged, largely pre-existing and
concurrent edits); six new implementation/test files pass formatting. No mass formatting.
Impeccable engine unavailable in its configured cache, UX skill CSV absent; text
references and established UI were used. Cached OpenAPI generator7.13.0 used when
npm network resolution stalled. No paid semantic prompt or production deployment.

## Local runtime

API8007 was restarted only after road scenario, analysis and stress queues were idle.
PID1751, /tmp/plexus-connectivity-api.log, GRAPH_DIR root/data, CHAT_ENABLED=true,
ROAD_WORKERS=6 retained. Initial graph loading took longer than the first health check;
a redundant foreground startup subsequently failed to bind and shut down safely.
The original new background process remains healthy; OpenAPI includes both table types.
UI5187 remains running. No source database modification from the new calculation.

Next optional work: evaluate the skill choice with an explicitly authorized live LLM
prompt. Current implementation and deterministic protocol tests do not prove semantic
routing for every free-form prompt. Preserve unrelated ongoing changes.

## Area representation review, 2026-11-11

User asks whether both reported times represent settlement road-node clouds and
whether this should be redesigned. Verified connectivity.access uses one stored
node/snap per settlement for both scenarios. Current graph locations/points schema
has no settlement polygon or population distribution; graph nodes have coordinates
but no settlement membership. A multi-point territorial model is not connected.

Recommendation for settlement-wide accessibility: spatially distributed residential
sample points/zones inside verified settlement/built-up boundaries, weighted by
population when available. Otherwise label the equal-area/sample-weight assumption.
Compute point-pair travel times on the full network, aggregate the existing decayed
scores with fixed weights, preserve unreachable pairs, and report reachable share
and travel-time distribution separately. Freeze points and weights before comparing
closures. Do not replace settlements with freely connected supernodes or take only
the fastest edge-to-edge path, which measures the best access case and can hide
harm to other neighborhoods. Uniform raw OSM-node weighting reflects digitization
density rather than resident distribution. Existing point-to-point result remains
useful if labelled as such. No model/code changes during this advisory review.

Primary guidance: FHWA, Traffic Analysis Toolbox Volume XII, chapter4, Model Refinement
Data (Traffic Analysis Zone Splitting), recommends reviewing zone size and adding
connectors or splitting zones near the affected corridor:
https://ops.fhwa.dot.gov/publications/fhwahop12009/sec4.htm
The weighted point-sampling design above is our proposed adaptation, not a claim that
FHWA specifies this exact index. Branch feat/map-first-ui, HEAD cdb2c2e.

## Closure congestion limitation, 2026-11-11

User flags the R-217 Kavkaz bridge example: rerouting a large trunk-road flow onto a
narrow local detour could congest it, so +2.7 minutes may be misleading. Code review
confirms changed_weights sets closed ways to infinity and leaves all other edge
weights unchanged. It does not transfer traffic onto detours, reassign OD demand,
model congestion feedback or queues. evaluate_road uses stored confirmed flow only;
unknown flow remains free-flow. Even measured baseline flow on a detour would not
include newly diverted traffic in the current closure calculation.

Therefore 19.6/22.3 minutes describe point-to-point routing at fixed baseline edge
costs; they are not a traffic forecast after closure. No actual R-217 hourly volume,
detour lane count or diversion share was verified during this review. Congestion
assignment is a separate limitation from representing settlements with more points.
A future model needs OD/local/transit demand, road/junction capacities, reassignment
and, for queues, a time horizon. Without observations, use clearly labelled demand
scenarios instead of silently asserting flow. No code or traffic-data search started.
