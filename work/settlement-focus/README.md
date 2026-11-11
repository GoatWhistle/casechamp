# Settlement focus, 2026-11-11

Branch `feat/map-first-ui`, HEAD `cdb2c2e1108bde7ff37ab91f9d7907d05de2a897`.
No commit, push or deployment. Preserve concurrent road stress, chat window and legend work.

## Behavior

The existing `present_atlas` accepts `kind=settlement` and an exact settlement ID.
`query_atlas` resolves names; the server resolves coordinates and parent region through
`SettlementQueries.location`. Invalid/missing coordinates emit no map event. Caller-supplied
coordinates are rejected. The runtime presentation skill covers settlement focus without
adding another model-visible tool.

The frontend accepts `focus_settlement`, selects its region and zooms to 12 with a named
point marker. Replaying the answer restores the focus. Reset/region selection/session
change clears the marker. Existing motion duration, interruption and reduced motion apply.
Eastern negative longitudes use the existing map's wrapped coordinate convention.

## Real data evidence

`command.json` was generated through the real search/repository/use-case path against
local ClickHouse. Aleksandrovskoye in Stavropol Krai: `07502000101`, parent `07000000`,
43.00495 longitude, 44.71057 latitude. The sparse `atlas_points` table has 7682 rows;
`atlas_settlements` has 155412. Point lookup therefore also joins full settlements to
`plexus_graph.locations`. Missing coordinates remain an explicit error.

## Checks

- Backend Ruff passed, mypy passed for 240 source files.
- Backend unit suite: 335 passed with `--import-mode=importlib -n 0`; the default collection
  briefly failed because concurrent road stress and corridor tests shared `test_routes.py`.
- Real ClickHouse integration suite: 46 passed.
- Frontend `npm run verify`: 36 rule checks, typecheck, lint, 453 tests and production build passed.
  Existing PostCSS `from` and large-chunk build warnings remain.
- Settlement desktop E2E uses real settlement/location API responses and a deterministic chat
  stream fixture. It does not test paid model intent selection. Final functional E2E: 2 passed
  in 25.1s on the production preview, normal and reduced motion. Focus, stored center, zoom,
  popup name, replay after manual zoom, parent-region URL, reset and zero page errors passed.
  The initial complete normal-motion dev run also passed its full-page axe check (0 violations).
- Desktop screenshot: `desktop-1440.png`; inspected at 1440×1000. Mobile checks omitted per instruction.
- `git diff --check` passed.

## Local runtime and recovered failures

API `8007`, PID `96218`, log `/tmp/plexus-settlement-focus-api.log`; health 200 and updated
OpenAPI includes `SettlementMapTarget`. UI dev server remains `5187`.
Restart was performed only after verifying no queued/running road scenarios or analyses.
An initial launch resolved the venv interpreter symlink and lost its environment; corrected
to the absolute venv executable path. Startup exceeded the short health wait, then completed.

Docker was already starting during early coordinate lookup; ClickHouse recovered without
any restart by this task. npm type generation initially hit sandbox DNS restrictions, then
succeeded with authorized network access. Impeccable engine launch and ui-ux CSV lookup were
unavailable; existing project components and skill guidance were used.

Initial E2E fixture omitted required stream text/code defaults; corrected. Axe first observed
an exiting tooltip outside a landmark; test now waits for tooltip dismissal. Dev-server runs
were subsequently interrupted by mass HMR updates and a `LocaleProvider` error in the root
error boundary. Final verification uses a separate production preview to isolate those updates.
Production screenshot retries hit the overall browser timeout. A temporary attempt to turn off
the road layer waited on the custom checkbox label hit area; removed that unrelated step.
The final functional tests retain default road-layer behavior and avoid repeating the visual audit.
The temporary preview is stopped after the final run; the user dev server/API stay running.
