# Analyst skills and rail/air economics

2026-11-11. Branch feat/map-first-ui, base cdb2c2e. Preserve all pre-existing changes.
User: «ну сделай чтобы он отвечал правильно. ТО что нужно».
Steering: «оформи как скиллы просто. чтоб не отуплять агента. Плюс добавь ему рук к ж и авиа если такого нет».

Implemented five runtime skills under backend/src/app/adapter/chat/skills, discovered
by frontmatter and loaded through load_skill. Gateway includes the catalog, not skill
bodies. No keyword routing, canned economic answer, new dependency or model change.
Skill bodies remain product assets after root skills/ cleanup. Docker copies src/.

Economic guidance separates transport appraisal from company turnover and GDP/GRP,
reuses saved job evidence and asks for missing OD/value/cost inputs. Accessibility
guidance explains index units, fixed historical normalization and input-only coverage.
Rail/air capabilities already existed; preserved add/remove/airport closure and added
appraisal to the same scenario job. Economic inputs are limited to one region/call.
Listings disclose snapshot scope and possible truncation. Frequency and directed
service edits are still unsupported, explicitly stated in the skill.

GraphModelInfo flows through the engine port into calculation_capabilities and
transport listings, replacing the hardcoded old snapshot description. Live source
road-8033092fca2cf5fa, road-capacity-v1, intercity_in_road=true. The snapshot query
has no index-model label and honestly returns unknown. Its graph revision and cost
method remain available. No graph tables, source data or saved jobs were changed.

Checks: Ruff, mypy212files,309unit,45realClickHouseintegration passed. All five
SKILL.md files pass quick_validate. FunctionModel checks actual skill-tool exchange;
transport tests cover appraisal forwarding, multi-region misuse rejection, combined
airport closure and truncated listing scope. Initial targeted transport tests failed
with unexpected appraisal keyword before the change, then passed. One throwaway
live-inspection command used an incorrect graph module import; corrected to the
existing graph_snapshot module and rerun successfully.

Live API restarted only after both scenario/analysis queues were idle, same settings:
CHAT_ENABLED=true GRAPH_DIR=data ROAD_WORKERS=6, localhost8007. PID66341, log
/tmp/plexus-agent-skills-api.log. Health passed. No paid LLM calls, new scenarios,
mobile checks, commit, push or remote deployment. No claim of semantic response
accuracy from the deterministic FunctionModel test.

Manual semantic acceptance cases, not run against a paid model:
- Explain Stavropol Hansen and economic contribution: distinguish transport effect
  from regional turnover, do not substitute turnover for the asked effect, explain
  that 100% coverage concerns input population with model paths.
- Ask for an earlier economic scenario: discover/read its existing job and use the
  recorded appraisal and baseline, without submitting a duplicate calculation.
- Add or replace a Moscow-Tver train time: resolve model endpoints, inspect network
  capabilities, submit one joint removal/addition when replacing, read actual status.
- Close Surgut airport: remove all matching intercity air links using the wildcard,
  evaluate the requested atlas regions, preserve source schedules.
- Ask for rail/air project rubles: use supplied regional appraisal inputs; ask only
  for missing assumptions. Never infer demand or money from Hansen/population.
