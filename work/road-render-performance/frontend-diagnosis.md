# Frontend road rendering diagnosis, 2026-11-10

Scope: requested investigation and optimization recommendations. Product source unchanged.
Branch `feat/map-first-ui`, HEAD `c82ab1e`; existing uncommitted work preserved.

## Reproduction

Run `node work/road-render-performance/browser-probe.mjs` from the repository root.
It opens a separate headless Chrome at 1440×900 against frontend5187/backend8001,
injects observation into the served map module without editing product source, and records
resource timings, long tasks, source updates and CPU profiles. Real API data is used.
It checks the diagnostic budget of no main-thread task above100ms. The check fails on the
current implementation. This is a performance reproduction, not a passing verification.

Two corrected runs: `browser-run-1.json` and `browser-current.json`. CPU profiles describe
the final run. Initial exploratory runs were discarded: returning a Map instance from a
Playwright evaluation serialized its entire object graph and introduced artificial seconds
of delay. Evaluations now return undefined. No conclusion uses those discarded times.

The first corrected run measured:

| Scenario | Lines | Decoded road payload | HTTP resource duration | setData completion |
| --- | ---: | ---: | ---: | ---: |
| Country | 79433 | 16.40MB | 1.416s | 755ms |
| Center40.5/55.5, zoom7 | 49326 | 10.91MB | 0.822s | 321ms |
| Subsequent20px horizontal pan | 39954 | 8.94MB | 0.951s | 307ms |
| Komi | 8294 | 1.70MB | 0.440s | 90ms |

Country road update coincides with a421ms main-thread task; zoom/pan updates with179/158ms.
CPU samples identify MapLibre worker-message serialization (`qc`/`sendAsync` in the installed
bundle), plus smaller React/road list work. setData's synchronous return is nearly immediate;
its queued work and promise completion are separate timings. Promise completion is not a
pixel-presentation timestamp. Resource timings include local proxy/network contention.
These are development-build, instrumented headless measurements, not production FPS claims.

Komi links returned263420decoded bytes in401ms, producing52display lines. A cancelled
development-mode duplicate has responseStart0 and must not be interpreted as negative TTFB.
This regional sample does not establish performance for every region or the model-links toggle.

Independent existing API probe passed: reference bbox38,54,43,57 at zoom7 returned29765lines,
6773525decoded bytes in0.470s. The browser viewport is different. An identical browser bbox
compared via concurrent HTTP calls took1.482s on8001 and1.647s via5187;8003 took2.389s and
returned a slightly different fallback result. Do not confuse the separate airport preview
5189/8003 with the ClickHouse-backed5187/8001 environment.

## Findings

1. `frontend/src/entities/road-graph/road-viewport.ts` rounds bounds to0.0001degree. Small pans
   therefore produce new query keys. There is no buffered coverage reuse or spatial tile cache.
   Existing keepPreviousData prevents blanking, but does not avoid another request.
2. `use-road-layer.ts` creates a whole FeatureCollection and calls setData for every new view.
   Tens of thousands of features go through worker serialization and indexing again.
   Feature IDs are array indexes, unsuitable as persistent identities for cross-viewport diffs.
3. Road detail already varies by zoom on the backend, but overview lines retain full geometry.
   The country overview is still16.4MB decoded. This is a display-data size issue, independent
   of whether analytical storage is ClickHouse or another database.
4. Requests start at moveend. Layer detail then waits for the complete JSON response; simply
   spreading drawing across frames cannot reduce this initial wait.
5. `road-selection.tsx` maps/deduplicates every road to display only12choices on each render.
   CPU profiles show measurable but secondary cost. Use memoization and a bounded scan with
   an explicit policy for duplicate ways. Do not claim it is the main bottleneck.
6. The current transit hook already memoizes its collection. In the measured Komi scenario,
   transport connections are much smaller than roads; bulk progressive drawing has little
   justification there. Cache immutable link results by dataset version/season and avoid
   unnecessary repeated transformation when adding airport metadata.

## Recommended order

1. Reuse a buffered viewport until the visible bounds leave it or the detail level changes.
   Quantize request bounds to spatial cells, retain a bounded cache, abort superseded work.
   Keep prior geometry visible during replacement. Check small pans cause no new requests.
   Memoize the12road choices and avoid needless scenario-overlay setData on viewport updates.
2. Progressive display: load a lightweight overview first; after camera movement settles,
   add detailed visible-area geometry in bounded chunks/tiles, prioritizing visible center.
   Schedule bounded preparation between frames and cancel obsolete batches. Preserve selected
   roads and maintain an honest loading/detail indicator. Simplify display geometry by zoom;
   retain original topology and coordinates for routing/index calculations.
3. Prefer prepared vector tiles for the durable implementation. They provide spatial loading,
   independent caching and level-specific display geometry. Keep selected roads/scenario changes
   as small dynamic overlays and preserve stable source IDs for clicks and backend calculations.

Do not append increasingly large FeatureCollections through setData for every batch: that
reprocesses previous chunks repeatedly. A temporary GeoJSON incremental design can use updateData
with stable unique segment IDs and bounded queued work. way_id alone is not guaranteed unique
for disconnected chains; define a stable segment key before adopting diffs.

Primary references checked2026-11-10:

- [MapLibre large-data guidance](https://maplibre.org/maplibre-gl-js/docs/guides/large-data/)
- [GeoJSONSource setData/updateData](https://maplibre.org/maplibre-gl-js/docs/API/classes/GeoJSONSource/)
- Installed MapLibre6.17.0 source inspected; it passes objects through worker messaging rather
  than the older JSON.stringify implementation described in historical issues.

Acceptance for implementation: small pan inside cached coverage causes zero road requests and
zero whole-source replacement; interaction remains responsive while details arrive; canceling
a move never applies stale batches; IDs, selection and graph coverage remain correct. Repeat
the diagnostic in a production build and an interactive desktop browser before making speed
or frame-rate claims. No product tests/build were run because product code was not changed.
