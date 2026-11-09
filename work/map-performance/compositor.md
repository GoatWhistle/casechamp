# Compositor-only map gestures, 2026-11-08

Follow-up to [followup.md](followup.md) after the user reported that zooming in and out still lagged.
Baseline: committed `377e1e8`, served on stand 8080. Candidate: working tree on top of `377e1e8`.

## Diagnosis

`zoom_probe.py` (Chromium 156.0.8078.4 headless, 1440×900, DPR 1, CPU throttle ×4, real API, production
build) traced three human-like scenarios on the baseline:

- Trackpad, 140 wheel events of ±6 px: no long tasks and 17 ms rAF frames, but 6.0 s of raster worker
  time during a ~3 s gesture. `will-change: transform` on the SVG `<g>` did not create a composited
  layer, so every frame re-rasterized the map. rAF timing hid this because raster runs off the main thread.
- Mouse wheel in bursts with 300 ms pauses: 1 177 `d` attribute swaps. Every pause longer than the 180 ms
  settle delay above scale 2 switched all 83 shapes to full geometry and the next tick switched them back.
- Zoom buttons: 841 `d` swaps and click tasks up to 84 ms. A CPU profile on an unminified build with
  source maps attributed them to `refine` → `setAttribute`, a forced `getBoundingClientRect` in
  `camera.begin`, `getComputedStyle` in `motionMs` per flight, and re-rendering `MapZoom`/`Tooltip`.

## Change

- Both SVG layers live in a permanently promoted HTML wrapper (`data-map-stage`). Wheel, drag, pinch and
  flights only set the wrapper transform from the last committed view (`viewShift`). The `<g>`
  transform, culling and stroke widths change only at commit, or when the gesture has zoomed by 2.5× or
  to 0.4× of the committed scale.
- SVGs paint outside their box; shapes within one viewport of margin stay visible, and flights extend
  this cover along their path, so zoom-out and pan do not show empty edges before commit.
- Detail level is chosen only at commit and applied only to shapes inside the viewport.
- Flights and button zoom skip the layout read; the flight duration token is read once on mount; the
  zoom controls element is memoized.

## Results

Same scripts, same machine, one run each. Raster is aggregate worker time, not latency.

| Scenario | Baseline 8080 | Candidate |
| --- | ---: | ---: |
| Trackpad raster | 5 992 ms | 59–68 ms |
| Mouse bursts raster | 1 240 ms | 573–642 ms |
| Mouse bursts `d` swaps | 1 177 | 51 |
| Button zoom raster | 4 216 ms | 717 ms |
| Button zoom `d` swaps | 841 | 45 |
| Button zoom long tasks | 84, 65, 61, 52 ms | 67, 64, 58 ms |

`stress.mjs` from the earlier follow-up (CPU ×6, DPR 2, copied with only its import and output paths
changed): wheel p95 33.4 → 16.8 ms, raster 6 312 → 892 ms, paint 211 → 25 ms; drag raster 127 → 37 ms;
hover unchanged within noise (p95 50 ms in both). Its single 117 ms wheel frame appears identically in
both versions; the trace-based probe of the same 180-event sequence shows no frame above 33 ms, so it is
treated as unexplained, not as fixed.

Visual check at 1440 and 375 px: mid-zoom-in (blurred, thicker lines until commit, as documented),
zoom-out to 0.5× and a 500×360 px drag show no empty edges; settled views are crisp.

## Verification and limits

- `npm run verify`: 36 rules, TypeScript, Biome, 353 unit tests, build. 13/13 Playwright tests on the
  production preview, including the rewritten gesture test (no `d` mutation during a gesture, stage
  transform reset after release).
- Stand 8080 rebuilt with `/tmp/plexus-map-compose.yml`; the probe on 8080 reproduces the candidate numbers.
- Headless software raster only. The user's browser, GPU, DPR and physical touchpad are unverified.
  Button click tasks remain around 60 ms at CPU ×4 (React commit and style recalculation).
