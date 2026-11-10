## Streaming map chat, 2026-11-10

Branch feat/map-first-ui, HEAD 63fb9cb44f4fe53ce16c7d64e571bca234fb0135. Implemented Pydantic AI v2/Codex account Responses gateway, gpt-6.1-sol, right chat, Markdown normalization, structured tables/bar charts from atlas tools. Local preview5187 proxies chat8001; CHAT_ENABLED=true, personal login stays server-side. Real text and chart/table requests passed. Evidence and known baseline failures: [chat verification](../work/screens/map-chat.md). No commit/push. Next: user review; shared deployment needs its own auth policy. Protected instructions exceed SESSION target.

## Map actions and math, 2026-11-10

Same branch/SHA. Added MathML normalization, validated map tool events, single/group focus, zoom/reset and replay;900ms interruptible map flight with reduced-motion support. Live single/group focus verified. Details and final checks: work/screens/map-chat.md. No commit/push; local backend8001/frontend5187.

## Calculation tools, 2026-11-10

Same branch/SHA. User asks road-project scenario recalculation and PostgreSQL architecture. National graph and DuckDB absent locally; case.vm DNS fails. Asked for source graph/server location; full road-edge recalculation remains blocked on that input. Added usable exact uniform-time sensitivity (scales.5/1/2, not project effects) and pilot route tools; live Volgograd sensitivity passed. No PostgreSQL migration. Details/checks: [calculation tools](../work/screens/calculation-tools.md). Preview5187/backend8001. No commit/push.

## Graph release restored, 2026-11-10

Fetched origin; local feat/map-first-ui/63fb9cb unchanged, origin nowbbfa108. Downloaded release data-20261107 graph and DuckDB into data/; SHA256 and all edge references/weights verified. Full report: [graph restoration](../work/screens/graph-download.md). Missing-data blocker resolved, but snapshot is older:3 scenarios/84 regions, no operating_season or model metadata; Volgograd road93.79 vs current61.55. Do not mix baselines. Next: reconcile model snapshot before national road scenario worker. Current app untouched; no commit/push.

