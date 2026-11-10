# Remote review, 2026-11-10

Read-only fetch/review: local HEADc397ca6, origin/feat/map-first-ui ee9494a.
Six new commits:0d812dc,4a38df9,89e1009,9ce7a6b,e48a095,ee9494a.
Settlement endpoint selection in scenario lab, from_id/to_id API, point_id.npy required,
per-settlement impact output, chained endpoint relaxation. Market-city pairs update full
market matrix; settlement links affect named endpoints/chains only, not other settlements'
transit through them. This restriction is explicit in code, tests, docs and UI.
Last commit removes additions from old pilot but retains the pilot itself, unlike local removal.
Formatting-only backend changes also included. No merge, tests, source changes or push.
Future integration must preserve local national graph diff and removal of legacy pilot;
new scenario artifacts require point_id.npy. Raw remote tests reviewed, not executed.
