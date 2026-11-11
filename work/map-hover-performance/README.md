# Pointer performance, 2026-11-11

feat/map-first-ui HEAD cdb2c2e. User reports cursor stutter over the map.
Used diagnosing-bugs and fixing-motion-performance.

Hypotheses: repeated delegated MapLibre hit tests, forced layout in hover-card placement,
and region repaint on hover. Instrumentation confirmed redundant hit tests and a
write-before-layout-read path. No evidence justified changing graph data or new visuals.

Same Chromium1440x1000, real API8007/Vite5187, region18000000, wait for road rendering.
Three synthetic bursts of120 mousemove events each; timed through two animation frames.
Before: 594 queryRenderedFeatures calls per burst;278.1/303.8/349.7ms elapsed.
After:1 query per burst;33.1/32.5/34.4ms elapsed. Query CPU34.5/11.3/12.9ms before,
3.0/0.8/0.8ms after. These are event-burst microbenchmarks, not user FPS or hardware
cursor-latency measurements. Main-thread spikes under high pointer event rates reduced.

Combined region/airport hit testing uses latest coordinates once per animation frame.
No delegated mouseenter/mouseleave handlers trigger their own hit tests. Airport popup
updates only when the airport changes. Hide on camera movement/exit; cancel pending
frames and remove listeners on disposal. Hover-card geometry is read before style writes.

Regression test failed before fix, passes after: tests/entities/region/map-hover.test.ts.
Browser check covers region tooltip, airport popup and exit cleanup. No paid calls,
backend/data changes, commit or push. New UI and graph geometry preserved.

Final checks: npm run verify exit0 (36 rules, typecheck, Biome,469 tests, build).
Browser: region tooltip1, airport popup1, popups after leaving0; no JavaScript errors.
