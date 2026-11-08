# Map and navigation repair, 2026-11-08

This document records the first repair. The user subsequently reported remaining lag, locked home-scale panning and an incorrect Arkhangelsk camera focus. Current implementation and follow-up evidence: [followup.md](followup.md). The earlier completion statement below does not establish that those later regressions were fixed.

## Request and source

Continue Claude session `393d291b-93d0-462e-8a29-4e5109354f6c` in this repository. Its last task was to fix map zoom/performance and scrolling/navigation in the top tabs on `feat/frontend`. The session stopped after diagnosis and probe creation, before product edits. Baseline: `5e21c352168292fe16075aa489bcda4a905594be`.

## Plan coverage

| Item | Implementation |
| --- | --- |
| Native nonpassive wheel, deltaMode, pinch, horizontal pan, Safari gesture suppression | `use-map-gestures.ts`, `map-gesture.ts` |
| Composite during gesture; commit SVG once at idle/release | `use-map-camera.ts`, 180 ms settle token |
| Cursor outside React state, delegated region events, stable props and memoized panels | `use-map-hover.ts`, `russia-map.tsx`, map feature components |
| Selection outline computed once, waves unmounted after completion | `selection-waves.tsx`, parent completion callback |
| Two-pointer pinch and bounded pan | gesture hook and view constraints |
| One overlay SVG, temporary wrapper promotion | map component and camera cleanup |
| Two exported geometry detail levels | mapshaper script, low-detail JSON, API field, frontend threshold |
| Tab scrolling and navigation | document scroll for region table; top nav avoids full-page snapshot transitions |
| Additional observed bug: reset when nothing selected did nothing | reset always invokes camera reset as well as clearing selection |

## Measurement

`probe.mjs` runs Chromium 156.0.8078.4 headless at 1440×900, DPR 2, against a production Vite preview with the real atlas API. Exact browser version and timestamps are in JSON. Each named scenario ran once before and once after, following the same script. Twelve wheel ticks, thirty drag moves, sixty hover moves, twenty scroll ticks, and five navigation transitions. No CPU throttle. Timings include the action and a 600 ms settling window. RasterTask is aggregate worker time, not elapsed time or a user latency percentile. Frame samples include settling frames. This is local evidence, not a hardware-wide FPS guarantee.

Run from the repository root with a preview/API already running:

```bash
node work/map-performance/probe.mjs after.json
node work/map-performance/visual.mjs
```

Override `PROBE_URL` and `CHROME_PATH` for the performance probe when needed. Before/after traces are summarized in `before.json` and `after.json`.

| Scenario | Before | After |
| --- | ---: | ---: |
| Map Ctrl+wheel default prevented | false | true |
| SVG commits, 12 wheel ticks | 12 | 1 |
| SVG commits, 30 drag moves | 30 | 1 |
| RasterTask, wheel | 364.6 ms | 139.6 ms |
| RasterTask, drag | 343.3 ms | 72.7 ms |
| RasterTask, hover | 334.7 ms | 55.4 ms |
| RasterTask, selected region wheel | 451.6 ms | 137.3 ms |
| Navigation frames longer than 50 ms, five transitions | 55 | 0 |
| Region-table scroll after twenty ticks | inner table 2400 px | document 2400 px |

Other routes' steady scrolling had no >50 ms frames in either run. `/sources` fits in the desktop viewport, so no scroll is expected. We did not infer a general scrolling performance bug where measurements did not show one.

## Motion review

| Before | After | Why |
| --- | --- | --- |
| SVG group updated on every input | HTML wrapper transform once per frame | avoid geometry/raster work on every input |
| Permanent promotion on three overlays | one overlay and temporary wrapper promotion | reduce persistent layer memory |
| Whole-page snapshot on each top tab | immediate top navigation | preserve input and avoid snapshot stalls on frequent navigation |
| Camera interruption used the previous goal | matrix of visible layer is converted back to map coordinates | new gesture starts where the user sees the map |

Approve for the tested Chromium scenarios. Rare region flights retain the existing map duration exception; direct manipulation does not tween. Keyboard zoom/reset is immediate, reduced motion skips camera flights. Browser checks cover touch pinch, pointer release, interruption, reset without selection and SVG commit counts.

## Limits and check history

- Original regression test failed because wheel events did not prevent the browser default, then passed after the fix.
- An added unit test initially distinguished negative zero from zero; the assertion now checks the numeric boundary.
- Playwright JSON imports required an explicit import attribute; the first invocation stopped before collecting tests. Corrected and rerun.
- The visual script initially used browser.newPage; axe requires an explicit context. Corrected and rerun.
- `npm run verify`: 36 repository rules, TypeScript, Biome, 345 tests, production build passed. Existing PostCSS `from` warning remains.
- Backend: Ruff, mypy and 104 unit tests passed. `pytest tests/integration` collected no tests and exited 5; it is not reported as passing integration coverage. Browser tests exercise the real API and checked-in files.
- Geometry: all 83 shapes retained. Low-detail polygons omit some small rings; 15 intersections were reported by mapshaper. Original detailed paths are unchanged. See `docs/api.md`.
- Physical touchpad, mobile Safari and physical phone have not been tested. Pointer pinch is exercised through Chromium CDP. Safari gesture cancellation is implemented but not browser-verified.
- `PRODUCT.md`/`DESIGN.md` remain template placeholders; styling follows existing tokens/components and the actual UI. Impeccable launcher lacked execute permission; ui-ux-pro-max's CSV database was absent. Existing project rules were used directly.

Visual pass: six routes at each of 375×900 and 1440×900 (12 cases) had no axe WCAG A/AA findings, JavaScript page errors or document horizontal overflow. Map, selection and table screenshots were inspected. At 375 px the region table retains its horizontal scroll. Large Krasnoyarsk boundaries, long region names, null metric values, extreme zoom, touch pinch and missing index are included in the real-data/gesture checks.

Primary API references checked for gesture semantics: [MDN wheel events](https://developer.mozilla.org/en-US/docs/Web/API/Element/wheel_event), [MDN pointer pinch](https://developer.mozilla.org/en-US/docs/Web/API/Pointer_events/Pinch_zoom_gestures). Export options were checked with `npx --yes mapshaper@0.7.101 -help simplify`.

Final stand verification: both `app` containers rebuilt and healthy on UI `http://localhost:8080` and API `http://localhost:8001`. All 9 Playwright tests passed on port 8080 (18.4 s), including flight interruption and keyboard/reduced-motion handling. API through nginx returned 200 and low-detail paths for all 83 shapes. Temporary validation servers on 4173/8002 were stopped. Compose was kept at `/tmp/plexus-map-compose.yml` to respect the earlier removal of the repository Compose file. No commit or push was made.
