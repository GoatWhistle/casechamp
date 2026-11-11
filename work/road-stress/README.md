# National road stress implementation

User approved countrywide road-only stress tests, map and agent parity, actual detours,
compound closures and persistence. Do not narrow to a pilot. Do not collect traffic.
Preserve unrelated working changes. No commit/push/deployment requested for this task.

Implemented:
- Shared RoadJobs queue and up to 48 configured search workers; checks used 6.
- Whole-way closures preserve parallel ways, parent scenarios union the closures.
- Early connected-component check, unrestricted road shortest paths to 180 markets.
- Self-market excluded, preexisting disconnection and missing attachments reported separately.
- ClickHouse baseline arrays, normalized point/market impacts with SQL pagination/bounds,
  persisted job status and summaries. Explicit migration plus Compose schema service.
- API, selected road/scenario/point context, three agent tools, validated stream/history
  artifacts, saved routes and interactive cards. No paid model calls.
- Map closure geometry, national region shading, viewport point query capped at 200,
  clickable points/regions, endpoint search, actual before/after route geometry, map legend.
- History, URL reopen, cancellation, parent navigation and joint-impact comparison.
- Camera accommodates the floating chat panel; late geometry cannot affect another chat.

Measured evidence: docs/road-stress.md, docs/results/road-stress-checks.json.
- 155747 unique settlements, 84 source regions, 180 markets.
- 483 unbound points; 77 points with preexisting lack of external model markets.
- M-10 closure: 212.4s, 169 newly disconnected points.
- M-10 + M-11: 284.1s, 173 newly disconnected points.
- R-257: 283.6s, 98 newly disconnected points.
- All three expose 154899 points / 127754656 residents to a change in at least one market;
  this broad criterion is explicitly NOT traffic or road users.
- One-way negative control: no impacts; first baseline 248.6s.
- Torzhok–Veliky Novgorod route: 337.03km/4.194h -> 429.37km/5.626h.
- Queue cancellation and persisted cancelled status verified after API restart.

Checks:
- Backend full Ruff/mypy and 409 tests (unit + integration) passed.
- Subsequent lifecycle/script check: Ruff/mypy249files and12focusedtests passed.
- Final frontend verify:36rules/typecheck/lint/460tests/build passed.
- Final3desktopE2E passed in10.6s on immutable preview5190 after camera refinement: keyboard/axe, saved result/reload,
  real detour through both comboboxes and preserved closure geometry.
- Screenshots inspected at1440/1920. Mobile checks excluded per user instruction.
- Compose config --quiet passed. Docs link checker has an existing unrelated broken anchor:
  docs/economic-appraisal.md -> road-capacity.md#как-воспроизвести-подготовку.

Environment:
- User-authorized cache cleanup freed6.1GiB. No project backups/data removed.
- User-authorized Docker restart recovered ClickHouse; additive schema/integration tests passed.
- Validation API8817, CHAT_ENABLED=true; stable preview5190, devpreview5189.
- Primary API8007/UI5187 were not switched. Runtime has one stress queue owner; do not launch
  a second writer against live running jobs. No LLM prompt sent during verification.
- Old owned worker processes from stopped validation API were terminated; Docker volumes intact.

Limits:
- Whole country means all current source points; source completeness is not established.
- Road model is undirected/year-round and excludes passenger rail/air. Missing restrictions,
  real traffic and causal economic loss are not inferred. Own market cannot conceal isolation.
- National changed searches are full recomputation, not incremental shortest-path repair.
- Cold routes and first baseline can take minutes under load. Baseline and completed jobs persist;
  per-pair route cache is bounded and process-local.
- Paid semantic agent run, production deployment, mobile, screen-reader and slow-network QA
  were not performed. Old graph results cannot be re-routed against a new graph version.
- Dev HMR changed form state during one E2E attempt; isolated production preview passed all3.
- Early global checks encountered concurrent source/type/lint changes. Final checks use latest tree.

Final visual check: browser-camera-results/stress-detour-1440.png inspected; route fits free map area.
