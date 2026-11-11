# Compact agent connectivity contract — 2026-11-11

Request: make the previous traffic/economics functionality convenient and minimal
for the agent. Applied writing-for-agents; no new tool interfaces or calculation
changes. Branch feat/map-first-ui, base SHA cdb2c2e1108bde7ff37ab91f9d7907d05de2a897.
Preserved all concurrent working changes; no commit, push, paid model call or UI edit.

- settlement-connectivity: calculate / continue / answer, 847→330 words.
- economic-assessment: saved closure / regional project / business indicators,
  515→362 words. Keeps authorization of illustrative rates and evidence limits.
- road-scenarios delegates selected-group traffic rules instead of repeating them.
  Removed traffic-specific duplicate from always-loaded gateway instructions.
- calculate_scenario description shortened. manage_calculation exposes summary/full.
- Chat reply projection replaces way arrays with counts and removes repeated
  per-pair assumptions/empty segments. Exact numeric values, root assumptions,
  graph/method versions, unknown-lane counts and ID remain. Full saved JSON is
  unchanged and accessible with CalculationQuery detail=full. UI tables unchanged.

Checks: Ruff passed; mypy260source files passed; 375unit tests passed. Regression
covers summary/read equality, full exact stored payload, unchanged numbers and
assumption counts. Existing two-turn FunctionModel protocol passed. Real stored
bridge result:4232→2436characters (42.4% smaller), numbers unchanged.
See checks.json and summary.json. Before-skill copies retained for size comparison.
No schema migration, routing change or UI change: integration/browser checks from
the preceding traffic task were not repeated. Free-form paid agent not tested.

Runtime: waited for idle API8007, graceful stop14139, start21084 with workers6,
chat enabled. Log /tmp/plexus-agent-guide-api.log. Health confirmed HTTP200.

Final-check timing: after the full suite passed, concurrent national-impact edits
changed shared network_scenarios.py and controller/road_stress/router.py. A later
whole-tree Ruff check caught import ordering in both; shared chat imports sorted,
other task controller left to its owner. Scoped Ruff and connectivity protocol/detail
regressions rechecked successfully. Prior full-suite counts are a point-in-time result.
