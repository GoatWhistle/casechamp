# Local runtime record, 2026-11-11

Historical checks and their later corrections, preserved from the session notes.
The final authentication entry supersedes the earlier disabled-chat state. Frontend
check failures were repaired in the subsequent map-controls task.

## Current local launch, 2026-11-11

Fetched all origin branches/tags with pruning. The newest frontend commit is 78fdc0a
(2026-11-11 18:45:09 +0300) on feat/map-first-ui. Reset this branch to
origin/feat/map-first-ui, HEAD 5cd8921fb7b51e302d29a0cdd36deb6387611e00.
Discarded the old tracked session edit and untracked project files, including four root HTML
mockups and the prior frontend audit. Ignored environment/data files and existing DB preserved.

Built and started the full stack with
`docker compose -p casechamp --env-file .env.analytics up --build -d`.
Frontend: http://localhost:8080; API through /api/v1; ClickHouse: 127.0.0.1:18123.
All three services healthy. Existing DB volume: casechamp_plexus_analytics;
new derived-cache volume: casechamp_plexus_runtime. Docker manages restart/persistence.
CHAT_ENABLED=true after the local auth connection recorded below; no model requests made.
Published plexus_scenario tables remain empty.

Verified HTTP200 for /, health, overview, all82regions, road-scenarios and a real road-graph
viewport. Chromium1440x1000 renders the map and Summary with no page errors or failed API
requests. Screenshot: /tmp/casechamp-update-map-1440.png; smoke: /tmp/casechamp-update-smoke.json.
Docker frontend/backend builds pass. Backend Ruff/mypy pass;247unit tests pass in9.43s.
Initial sandbox unit run hung after90passes and was interrupted; normal-host rerun passed.
Frontend rules/typecheck pass; verify stops on formatting in
frontend/tests/entities/road-graph/link-changes.test.tsx. Separate Vitest run:434pass,1fail
in transit-geojson.test.ts:127, whose expected straight air link differs from the new flight arc.
Source left exactly as published. Logs: /tmp/casechamp-update-frontend-{verify,tests}.log and
/tmp/casechamp-update-backend-unit-unsandboxed.log. Full integration suite not rerun.
No further launch action required; fix those upstream frontend checks only if requested.
Only this session note changes tracked files. Protected user instructions exceed SESSION target
and are retained verbatim; superseded status entries were removed under compact-context.

## Manual testing readiness, 2026-11-11

> чего не хватает чтобы полноценно протыкать проект

Read-only check on the same branch/SHA: all Compose services healthy. Chat is disabled and
backend has no local auth.json; enabling requires provider authorization available to backend.
/scenarios returns503: its separate plexus_scenario snapshot is empty. Road scenarios use the
loaded national graph instead. Region17000000, accessibility comparison,19sources and graph
location search return200. Runtime has one road worker and only the baseline numeric cache;
a full intervention-to-result run has not been verified after this launch. No changes to runtime,
source or data; no model calls. Main gaps: chat connection and separate laboratory matrices.

## Chat authentication clarification, 2026-11-11

> мою авторизацию это что тебе апи ключ нужен или как

Local gateway uses AsyncCodex.account and OpenAICodexProvider. Installed provider reads
subscription tokens from Codex auth.json (honors CODEX_HOME) and explicitly never falls back
to OPENAI_API_KEY. Current integration needs a ChatGPT Codex login available to backend,
not a separate API key. Host login validity was not checked. No credentials read or changed,
no model call, no runtime change; same branch/SHA as the launch above.

## Local chat authentication connected, 2026-11-11

> я не понял в итоге что тебе скинуть чтоыб все заработало

Existing host `codex login status` reports ChatGPT login. Connected only the existing auth.json
file to backend at /home/app/.codex/auth.json, with a writable tmpfs for SDK runtime files.
No tokens copied, printed or committed. Ignored .local/compose.chat.yaml enables CHAT_ENABLED;
ignored .env.analytics sets COMPOSE_FILE=compose.yaml:.local/compose.chat.yaml to retain setup.
Same source branch feat/map-first-ui and HEAD5cd8921; no product source changes or commit/push.
Recreated backend. SDK account(refresh_token=True) succeeds inside container and provider loads
credentials successfully. All three services healthy; health through8080 returns200.
No model prompt sent, so a full streamed answer remains unverified. User need not send a key,
password or file. Chat-auth blocker resolved; separate /scenarios data gap remains.

## New connections explanation, 2026-11-11

> что такое новые связи обьясни и зачем вкладка расчет новых связей

Checked /scenarios UI and domain/market_scenario.py. New connections are hypothetical
bidirectional road/rail/air links with travel time and scheduled-service frequency. The separate
calculator compares modeled travel times and population-weighted Hansen before/after without
editing source data; it is not a financial return forecast. It overlaps the map Scenario tools.
The separate page still needs its missing plexus_scenario matrices. No code/runtime/data changes;
branch feat/map-first-ui, HEAD5cd8921 unchanged.
