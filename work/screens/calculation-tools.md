# Calculation tools, 2026-11-10

User requests national scenario recalculation and asks whether moving all graphs to PostgreSQL
makes on-demand computation possible. Branch feat/map-first-ui at63fb9cb; earlier chat/map edits retained.

Discovery: national ETL graph/access/index code exists and manifests describe a generated road
graph,155412 comparable origins and180 markets. Actual data/graph_ru and data/casechamp.duckdb
are absent locally. Only atlas index exports and Tuva pilot graph are available. Read-only ssh
case.vm failed DNS resolution; no remote mutation or database migration performed. Asked user
asynchronously for graph/database location or reachable host. Full road-project scenario remains blocked.

Implemented independent available work: tool capability discovery; exact regional uniform-time
sensitivity from exported half-life sums; pilot graph inspection and existing shortest-route
recalculation with closure/frequency changes. GET /api/v1/regions/{id}/sensitivity exposes same
use case. Agent instructions prohibit confusing cached sensitivity, regional index and pilot routes.
No made-up national road changes, no implicit50% project assumption, no interpolation at10/20%.

Formula: A(k)=sum_j M_j exp(-ln(2)*k*t_ij/2)=A_half_life(2/k).
Regional population aggregation commutes with this transformation. For k=.5,1,2 use4h,2h,1h
sums and fixed normalization recovered from baseline Hansen/A_2h. Preserve original coverage,
market weights and data version. This is NOT a graph edit or project-benefit forecast.

Recommended next architecture, not implemented: PostgreSQL/PostGIS owns versioned road geometry,
market weights and scenario overlays; calculation worker keeps a compact immutable CSR snapshot
and applies weight deltas. Small selected-origin scenarios and cached baseline can be interactive;
full national recomputation runs as a queued job with progress/cancel/result version. Do not cut
paths at regional borders. Keep road normalization fixed. Benchmark before promising latency.
References: https://postgis.net/documentation/faq/spatial-indexes/ and
https://docs.scipy.org/doc/scipy/reference/generated/scipy.sparse.csgraph.shortest_path.html.

Checks: ruff/mypy passed;28 targeted sensitivity/pilot/chat/architecture tests passed. Independent
OD test verifies scaled-time results, not a mirror of the ratio implementation. Frontend type/rules
passed. Full backend145 passed/5 known stale dataset-count failures. Full frontend verify remains
blocked by existing boundary-geojson.test.ts import ordering. Live checks recorded below.

Live Codex sensitivity request for Volgograd18000000/road_summer returned baseline61.550791,
scale.5 result216.475775 and scale2 result29.068986 (rounded to6 decimals). Agent explicitly
stated no route recomputation and no project forecast. Initial axe found heading-order and duplicate
landmark labels; normalized generated headings and rendered artifact cards as non-landmark divs.
Simplified sensitivity table to time/Hansen/relative change, preserving absolute delta in API output.
Frontend369 tests/build passed; known baseline lint/test failures unchanged. Screenshots in
/private/tmp/plexus-sensitivity-{1440,1920}.png; final compact view checked separately.

Final compact table: axe0 violations, no horizontal document overflow.
