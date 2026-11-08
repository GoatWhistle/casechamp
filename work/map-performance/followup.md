# Follow-up map repair, 2026-11-08

The user reported lag during every action, home-scale panning locked, and Arkhangelsk appearing displaced after the first repair. That repair's broad performance conclusion was insufficient.

## Reproduced defects and changes

- At scale 1 the old pan bounds collapsed to x=0/y=0. The new bounds permit panning in every direction while retaining at least 15% of the map frame. The browser regression failed on the old stand and passes on the new build.
- Arkhangelsk's full bounding box includes remote Arctic islands. Its mainland center was 12.94% of the frame width away from the camera center. Focus now uses the largest polygon by area, synchronously from the selected geometry. Original coordinates are unchanged. The browser test also clicks the mainland and checks its actual SVG screen matrix, independently of camera state.
- Region detail queries retain previous data while fetching. That previous region no longer controls the camera, and the selected-region panel displays a loading state until the returned ID matches the selection.
- Geometry is cached once. SVG paths have no pointer hit-testing; the map uses cached Path2D and bounding boxes. Hover is a single path in a separate SVG and cursor movement stays outside React state.
- Moving geometry uses exported low-detail contours. Off-screen shapes are hidden. SVG group CSS transform updates are batched to one rAF; stroke widths and full geometry settle after release. No `non-scaling-stroke`, animated waves or full-page navigation snapshots remain in this map flow. Promotion is temporary.
- Selection flights use the existing 260 ms panel duration and can be interrupted from their visible position. Keyboard/reduced-motion controls are immediate.

## Performance evidence and limits

`stress.mjs` runs Chromium 156.0.8078.4, 1440×900, DPR 2, CPU throttle 6, with the real API and a production build. One run per version; 180 wheel events, 90 drag moves, 90 hover moves; a 250 ms settling interval is included. The page starts with Arkhangelsk selected. Its camera focus differs between versions because correcting that focus is part of the change. These are local observations, not a guarantee for every browser or device.

The corrected probe starts frame sampling **after** tracing starts and stops it **before** tracing stops. Earlier files `stress-before*`, `stress-after`, `stress-svg-direct`, and Canvas variants recorded instrumentation startup/teardown too; their large maximum frame gaps cannot be used as product latency evidence. `stress-final` uses the corrected sampler but is the rejected SVG-attribute prototype. The old drag label said 180 although its loop has always performed 90 moves.

Current comparison: `stress-control.json` (previous deployed version) and `stress-svg-composite.json` (final implementation). Numbers are frame intervals, not event-to-paint latency.

| Scenario | Previous p95 / max | Current p95 / max | Frames >50 ms, previous → current |
| --- | --- | --- | --- |
| Wheel | 16.8 / 83.4 ms | 16.8 / 83.3 ms | 2 → 2 |
| Drag | 16.8 / 50 ms | 16.8 / 33.4 ms | 0 → 0 |
| Hover | 33.4 / 66.7 ms | 16.8 / 33.4 ms | 2 → 0 |

Wheel cadence did not improve in this measurement. Aggregate raster worker time increased, so this is not evidence of lower total rendering cost. The useful observed improvement is hover response, plus the functional pan/focus repairs and the shorter interruptible flight. Physical Safari, the user's browser and their device remain unverified.

Rejected alternatives: per-frame Canvas drawing and transformed Canvas snapshots produced worse frame pacing in this environment. They were removed from product code. Raw negative runs remain in `stress-canvas-*.json`; do not compare their uncorrected maximum frame intervals to the corrected final series. SVG transform attributes also used more main-thread style work than the chosen CSS transform.

## Verification

- `npm run verify`: 36 repository rules, TypeScript, Biome, 347 unit tests and build passed. Existing PostCSS `from` warning remains.
- All 13 Playwright tests passed on production preview 4173, including home-scale drag, mainland focus, actual geometry/hit-test agreement, detail restoration, native wheel cancellation, horizontal pan, reset, mobile pinch, flight interruption, reduced motion, tabs, table scroll and axe.
- Backend is unchanged in this follow-up. Earlier Ruff/mypy and 104 unit tests passed; the integration directory was empty, not passing coverage.
- Visual evidence: `followup-visual.json`, `followup-*.png`, 375/1440 px, six routes each.
- Primary API reference for coordinate hit testing: [MDN isPointInPath](https://developer.mozilla.org/en-US/docs/Web/API/CanvasRenderingContext2D/isPointInPath). [MDN drawImage](https://developer.mozilla.org/en-US/docs/Web/API/CanvasRenderingContext2D/drawImage) was consulted for the discarded Canvas prototype.

Final stand: frontend rebuilt with `/tmp/plexus-map-compose.yml`; frontend/backend healthy on 8080/8001. All 13 Playwright tests passed on 8080 (21.2 s). Visual pass: all 12 cases had no page errors, horizontal overflow or axe violations; home and Arkhangelsk screenshots inspected at both widths. No commit or push.
