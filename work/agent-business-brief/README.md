# Combined closure evidence and business interpretation

2026-11-11, feat/map-first-ui, HEAD cdb2c2e. Changes remain uncommitted alongside existing work.

The default agent closure previously ran only national road consequences. Regional Hansen
existed as a separate explicit branch and was not supplied when reading a saved stress result.
A regression test reproduced the missing index submission before the fix.

The default closure now starts both existing calculators. The index covers resolved corridor
regions plus explicit region_ids; parent closures retain their complete way set. Results are
matched by exact way set, graph version and pure road-closure scenario. Completed indices are
reused; failed/cancelled indices may be retried. Lookups inspect all saved jobs, independent of
the recent-list page. Legacy stress IDs can request missing regional indices without resolving
expired selections. The automatic review waits for the matching indices and groups both types
of evidence, without duplicated regional rows.

Optional places/traffic adds the existing conditional pair-load calculation to the same call.
Reads include matching saved traffic (latest 20 connectivity results), capacities, flow/capacity
ratios and queues. No load is inferred from residents or static route delays. These are pair
scenarios, not a calibrated regional traffic forecast or an exact queue-location model.

BUSINESS_BRIEF is shared by ordinary and automatic answers. It states the user's editorial
intent without fixing a checklist, answer layout, number of findings or business conclusions.
Road skill guidance explains combined tools, missing-index recovery and optional traffic.

Validation:
- Regression reproduced missing submit_closure call, then passed after the fix.
- Ruff and mypy passed. Unit suite: 403 passed. Integration suite: 48 passed.
- Real ClickHouse read verified stress 8ab724dfe43f4ee99c9e5dd328655b0d with matching
  completed indices for Novgorod, Moscow, Leningrad and Tver regions and detailed consequences.
  See live-evidence.json and review-payload.txt. No matching traffic result exists for that closure.
- Broad ruff format --check remains failing: 80 existing/work-in-progress files would be
  reformatted. No repository-wide formatting was applied. New modules/tests were formatted.
- No paid model run or new browser visual check. Existing frontend artifacts/polling are used;
  public HTTP schemas and frontend source were not changed in this task.
- Early checks hit a duplicate pytest module basename; the test was renamed. Added mock fields
  for the expanded read contract. Final checks supersede those transient failures.

Local API8007 (PID81209) was restarted after confirming no active road/stress jobs, preserving GRAPH_DIR,
CHAT_ENABLED=true and ROAD_WORKERS=6. See /tmp/plexus-agent-business-api.log. Health passed.
No deployment, commit or push. Next: optional user-driven chat check; old completed commentary
stays saved in browser history and is not rewritten automatically.

## Prior chat state archived from SESSION

feat/map-first-ui HEADcdb2c2e: connectivity template excluded from chat; data/history retained.
Other tables wait for message completion. See docs/design-decisions.md. npm verify passed (472 tests). No paid calls; browser visual check not rerun.
