# Economic appraisal implementation

User authorization: «мы можем пункты выше уже сделать ,» (2026-11-11).
Scope: multi-OD passenger time changes, explicit low/base/high assumptions, freight time and mileage costs, discounted project costs/benefits, UI and agent integration.

Design: pure domain appraisal with signed changes; observed/assumed provenance on supplied flows; no population-to-flow or Hansen-to-GDP conversion. Graph supplies passenger times for submitted OD pairs, including disconnected cases. Freight times/mileage must be explicitly supplied with provenance because the graph's passenger air/rail routes are not truck routes. Project costs occur at year0, constant real benefits/maintenance at year ends; no growth/residual value assumed. Incomplete requested travel evidence yields an unavailable aggregate, not zero.

Persist appraisal assumptions and result as optional top-level fields on RoadJob in ClickHouse. Add columns without rewriting existing job results. Keep legacy single-pair money input supported, disallow simultaneous legacy and new appraisal. UI extends existing scenario panel with shared form primitives and a readable table with low/base/high scenario selection; no new visual system or mobile checks. Agent calls same use case.

Sources: UK DfT TAG A1.1/A1.3, accessed2026-11-11. Use conceptual CBA/time-valuation framework, not UK unit rates or a claim of Russian regulatory compliance.

Verification plan: independent arithmetic fixtures for multiple flows, negative effects, missing connections, duplicate/invalid inputs, freight km/time, year-end discounting and zero-cost ratio; real HTTP/storage integration; desktop browser scenarios and axe. Preserve existing calculations and concurrent work.

Implementation decision: freight time/mileage are supplied separately with a source. The available passenger graph includes air/rail and lacks validated truck access constraints; it is not reused as an observed freight route. Values are constant real rubles in an explicit price year, user-selected real discount rate. Report scope is the supplied flow portfolio, not a claim of complete national demand coverage.

## Verification evidence (2026-11-11)

Backend: Ruff passed; mypy passed174source files;205unit tests and44integration tests passed. Frontend:36repository rules, TypeScript, Biome,420tests and production build passed. Build retains its existing large-chunk advisory. Logs are stored alongside this file.

Real-browser E2E first passed on two passenger OD pairs and one explicit freight flow, persisted through ClickHouse and reloaded in UI. First test attempts exposed hidden-switch and combobox selector mistakes in the test, corrected to target the visible label and actual ARIA role. The final rule check caught Cyrillic literals in the E2E: city names now come from the actual settlements API and test assumption descriptions are English. No checks were disabled.

Visual review at1440/1920found that three simultaneous monetary columns overflowed the sidebar. Results now default to the base scenario with an accessible low/base/high selector and a two-column table. Final E2E also exercises all three choices. No mobile checks per user instruction; no paid agent calls used by this validation.

[Recorded example](../../docs/results/economic-appraisal-validation.json): job05e9b2918ee342e1aa9869601458484e, graph data-20261107. Real graph times, synthetic traffic/rates/costs clearly labelled. Closed-form annuity recalculation independently matches all3scenario annual benefits,NPV,BCR at1e-10relative tolerance. Base annual gross benefit7,453,170.94RUB andNPV-64,503,647.01RUB; high scenarioNPV9,802,740.20RUB and discounted public-benefit payback year18. These numbers validate implementation, not a forecast.

Limits: only supplied flows; freight hours/km are explicit inputs, not derived truck routing. No measured traffic dataset, GDP conversion, induced demand, emissions or financial investor cashflow. API8001 was restarted only while idle; subsequent user calculations were allowed to finish without interruption. New optional ClickHouse columns were applied without rewriting past job results. Changes remain uncommitted on feat/map-first-ui; concurrent map/legend/corridor edits are outside this task.

A final full E2E retry initially timed out waiting180seconds for another user’s running job b217c537e87d4f02972134ee36b435a4. That job was never cancelled or interrupted. The saved-result selector/axe checks passed independently; full E2E retried after that job reached completion. See e2e-busy-queue.log.

Final full E2E passed in20.7seconds after the queue cleared: job b3e73f2b33944cf9bab271fd6af30541 completed,2passenger pairs/1freight flow, all3scenario selectors, persisted reload, no page errors or axe violations. Final screenshots at1440/1920are in this folder. No unresolved failed checks.
