# New frontend with local functionality

2026-11-11. Branch feat/map-first-ui, HEAD cdb2c2e. Upstream visual source 5cd8921.
No commit/push, backend/data changes or paid model calls in this task.

New map layout, resizable side panel, chat shell, scenario navigation, grouped road
selection and result/history components retained. Local API types, streaming events,
saved chat validation, connectivity prose, calculation review, settlement focus,
stress map layers, road profile changes and project appraisal restored.

Stress controls are a disclosure inside the new scenario home. Road profile inputs
live alongside the new speed selector; appraisal is optional in both road and new-link
flows. Result views preserve new presentation and add stored project appraisal and
road cost assumptions. Scenario history keeps both upstream scenario IDs and local
calculation/stress artifacts.

Schema generated with openapi-typescript@7.13.0 from openapi-input.json: current
backend/openapi.json plus the optional ScenarioCard/ChatStreamEvent.scenario contract
already present upstream. This accepts both versions without dropping local endpoints.
Regenerate from a unified backend schema once that upstream backend event is integrated.

Browser check: real API8007 via Vite5187, viewport1440x1000, region18000000.
19,355 road segments completed rendering; selected four segments, set lanes to4,
submit enabled, no JavaScript errors or HTTP errors from API. No calculation submitted.
Screenshot evidence: scenario.png and profile.png. First attempts used obsolete labels;
corrected selectors to the new accessible names. Graph completion awaited explicitly.

Tests cover mixed upstream/local SSE artifacts, dedicated calculation-review routing,
stress session persistence, connectivity zero/missing states, profile payloads,
settlement focus, calculation progress and deduplicated commentary.
Initial failures: old straight-flight assertion, obsolete dictionary keys, old collapsed
calculation expectations and incomplete test result fixtures. Fixed source compatibility
and adjusted tests to the retained new UI. Exact-copy upstream failures are superseded.

Limits: no new paid agent run, no end-to-end recalculation submission, no mobile check
(per current project context). Existing build emits large-chunk advisory.

Final validation: npm run verify exit0; 36 rules, TypeScript, Biome, 71 test files /
468 tests and production build pass. git diff --check passes. See verify.log.
