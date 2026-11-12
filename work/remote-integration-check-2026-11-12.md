# Remote integration check, 2026-11-12

2026-11-12 remote commit check: fetched origin; current feat/transport-scenarios-update
HEAD986ae0f5ee754b9e98f25e2e608b5bc37cbad507 equals upstream. origin/feat/map-first-ui
has 15 commits absent from HEAD, tip0c7cb89; regional-datasets has 2 absent commits.
No merge requested; existing dirty work preserved. Next: await user scope; no failed checks.
Follow-up: raw ancestry overcounts missing behavior. 78fdc0a frontend was imported via
5cd8921 and adapted in986ae0f; 898a25d scenario contracts/cards have local integration.
Later chat/title/auth and resizable-legend commits remain unported (confirmed source).


## Frontend replacement, 2026-11-11



User: «все что удалилось не пренеслось про рендер графа что могло сломаться кроме визуала».
[Functional regression audit and Vite fix](../work/frontend-upstream-sync/functional-audit.md).


[Scope, checks, schema, browser evidence and limits](../work/frontend-functional-merge/README.md).


[Measurements, browser checks and limits](../work/map-hover-performance/README.md).


[Profiles, tests and limits](../work/map-pan-performance/README.md).


New branch feat/transport-scenarios-update from cdb2c2e1108bde7ff37ab91f9d7907d05de2a897.
Publishing all nonignored local changes, preserving excluded root HTML prototypes and secrets.
Frontend verify and commit-hook backend unit tests run before push. Runtime restart remains separate.

Source inspection: 898a25d frontend/API contracts are integrated, but its backend scenario emission is not fully ported. Later chat/title/auth and legend-resize commits are absent. No merge or product changes performed.
