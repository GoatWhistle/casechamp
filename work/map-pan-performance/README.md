# Continuous pointer and pan performance, 2026-11-11

feat/map-first-ui HEAD cdb2c2e. Follow-up to work/map-hover-performance: the burst
microbenchmark improved but the user still reported stutter in actual interaction.

Profile: Chromium headless1440x1000, real API8007/Vite5187, national map after road
render completion.180 sequential mouse moves, then180 moves with button held.
CDP CPU sampling and RAF frame intervals; one before run and three after variants.
This browser uses software WebGL. Docker VM also had high CPU load; results are not
hardware-independent FPS guarantees. Main-thread CPU samples primarily attributed to
native rendering, plus MapLibre tile traversal; delegated hit tests were no longer the
main source of stalls.

Before: hover p9566.6ms, max433.3ms,11frames>32ms;10feature-state/repaint updates.
Pan p95216.7ms, max533.4ms,371frames>32ms.
Source-batching pass: hover p9516.8ms, pan p9533.4ms. Intermediate run overlapping
verification: hover/pan p9550.1ms; retained as evidence of variability, not discarded.
Final isolated run is preserved in confirmed.log.

Changes:
- At most six road sources/layers. First2000-segment batch unchanged; remaining
  segments spread over at most five batches. Sorting, all coordinates, IDs and click
  metadata retained. No road sampling, truncation or lower-quality geometry introduced.
- Hover-card dimensions/bounds measured on layout/resize/scroll, cached during pointer
  movement. Small mounted card promoted for transform; removed the extra RAF delay.
- Hover highlight waits for the existing80ms instant token after pointer movement.
  Region tooltips update immediately; crossing regions while moving no longer changes
  feature state or invalidates the whole WebGL scene. Exit, pan and disposal cancel work.

Regression:40001roads previously created21sources, now6; test also verifies all
40001unique feature IDs and original way IDs survive, firstbatch2000 remains.
Hover-card test asserts120position updates cause one geometry measurement and resizing
updates bounds. Hover-intent test verifies delayed highlight and listener/frame cleanup.

Validation:36 rules, TypeScript, Biome,471tests, production build pass; build retains
large-chunk advisory. No backend/data changes, paid calls, commit or push. Reload the
existing browser page to rebuild cached road render chunks under the new batching policy.

Final isolated run: hover p9516.8ms, max266.7ms, one slow frame; zero feature-state
updates/repaints during the continuous hover sweep. Pan p9566.7ms, max266.7ms.
Pan remains GPU-bound in software WebGL; do not claim all stutter is eliminated.
The profile comparison supports reduced overhead, not a universal60FPS claim.
