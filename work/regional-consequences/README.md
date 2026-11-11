# Concrete regional consequences — 2026-11-11

User wants concrete regional consequences and forecast metric changes instead of
Hansen definitions. Branch feat/map-first-ui, base SHA cdb2c2e1108bde7ff37ab91f9d7907d05de2a897.
Preserved concurrent dirty work, including new minimal background-result chat.
No paid model calls, commits, pushes or deployment.

Implemented:
- RegionalConsequences DTO in usecase, SQL aggregation of stored stress impacts.
- Lost origin-market links; cumulative >=30/60/120min settlement/resident exposure;
  originally <=2h changed links, same-cohort finite before/after means, separate lost
  routes, threshold crossings; five destination summaries and six named examples.
- All counts cover the full region independently of example pagination. Resident
  counts occur before expanding routes; means exclude lost routes with explicit
  sample counts; empty means remain null. FINAL prevents duplicate writes inflating totals.
- Existing summary API and inspect_road_stress_test share these fields. Exact atlas
  names and IDs accepted; unknown region422; pending/national consequences null.
  Completed effects cached per job+region. No schema migration or routing rerun.
- road-scenarios instructs consequence → comparable before/after → named examples;
  conditional delivery/travel implications, not unsupported service/economic claims.
- stress_test_roads(source_calculation_id=..., way_ids=[], selection_ids=[]) takes
  exact closures from a saved legacy calculation, validates pure-road closure and
  snapshot, reuses a matching stress job. Never substitutes viewport roads.
- Automatic CalculationReviews enriches legacy regional results only from an exact
  completed stress-job match (ways+version), read-only. No new job during auto-review.
- Small Markdown before/after tables allowed from returned values; no extra UI cards
  or new tool interfaces. OpenAPI/frontend types regenerated.

Verification:
- Full backend: Ruff, mypy271files,391unit tests passed at latest checkpoint.
- ClickHouse integration47passed; includes region filtering, repeated-write dedup,
  threshold overlap, distinct residents, comparable means and null lost routes.
- FunctionModel load-skill→inspect protocol checks regional scope, sample counts and
  named before/after data. Legacy transfer rejects nonclosure/stale-version inputs.
  Automatic-review regression checks exact matching, no stale/queued/unrelated match
  and no calculation submission. Paid free-form LLM behavior not tested.
- Full frontend verify36rules/464tests/types/lint/build passed after schema regeneration.
  No visible layout changes; no additional browser/mobile run. Existing build warnings.
- validate.py independently sums ALL3713Novgorod/8834Tver impacted points and matches
  SQL thresholds, populations, nearby lost/comparable/crossing counts and means.
- Real API name/ID reads exactly equal validated values; health200, unknown region422.
  api-checks.json captures these checks. Same714-way saved job95c3a442..., graph road-8033092fca2cf5fa.
- Novgorod:800points/76600residents with any finite delay>=60min;222comparable nearby
  links92.186→145.193min,49nearby links lost. Kresttsy→Veliky Novgorod83.072→281.988min.
- Tver:291points/32029residents>=60min;171nearby comparable links98.839→137.700min,
 26nearby lost. Vyshny Volochyok→Tver110.950→169.522min.

Scope: fixed-weight road-only closure, not traffic or regional demand forecasting.
Connections are settlement-market pairs, not road segments; exposed residents are
not trips/users. Nearby cohort includes recorded changed links, not all regional
travel; <1min crossings may be absent. Each destination can repeat residents.
No physical isolation, hospital access, jobs lost, GDP or money claim without evidence.

Runtime: API8007 initially31326 passed real API tests. A concurrent chat task then
replaced it with33945. Latest idle verified listener replaced gracefully with34705
for final legacy transfer and review enrichment; log /tmp/plexus-region-effects-api.log.
Final health200 and regional summary verified after restart (222 comparable,49 lost nearby connections). API8817 untouched; UI5187 and preview5190 use main8007.

Resolved checks: local npx API generator could not access registry (ENOTFOUND);
used installed openapi-typescript7.13.0 successfully. Initial shell glob/cwd and
nested-if lint failures fixed. Mid-task API connection refusal was a concurrent
restart (verified process state), not a calculation crash; no duplicate server started.
Artifacts: real-results.json, validation.log, api-checks.json, unit.log,
integration.log, frontend-verify.log. Public protocol in docs/results/regional-consequences-validation.json.
