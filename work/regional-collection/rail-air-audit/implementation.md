# Local integration, 2026-11-10

User clarified production means updating the local application, not remote deployment. Branch feat/map-first-ui, base HEAD c397ca6; preserve unrelated work. No commit/push.

Added optional network-links.json overlay, rail mode, endpoint lat/lon, is_model, include_unknown API query; generated OpenAPI/frontend types. Full directed OD records remain in API. Selected-region map draws schematic rail/air, default excludes models with explicit checkbox to enable them; UI lists model badge and original provenance. All imported records retain unknown season; source date periods are in notes, not inferred annual seasons.

Counts:33957 model records +135 UVT schedule records +4 Yakutia chains =34096 additions;46487 total links;76rail/67air regions. Exact emitted checksum/counts: frontend/atlas/public/network-links.manifest.json. UVT4 conflicting records excluded;14 otherwise eligible records outside atlas/unresolved endpoints skipped. Base atlas/indices untouched. No recalculation of graph/Hansen.

Verification: backend Ruff and mypy src pass;175 unit+integration tests pass. Full mypy also reports two existing typing errors in tests/unit/adapter/road_corridor/test_chat_calculation.py. Frontend verify passes36rules/typecheck/Biome/386tests/build; existing chunk/PostCSS warnings remain. Agent geojson checks cover reverse dedup, dateline, coordinates and >2000 links. Data review caught incorrect winter assignment; corrected to unknown and explicit API option. Visual check in user's desktop Chrome revealed unreadable all-model hairball; corrected with opt-in model layer. User active browser prevented controlled viewport test; no mobile checks per instruction.

Backend local8001 restarted with GRAPH_DIR=data and CHAT_ENABLED=true; existing cancelled analysis jobs preserved. Frontend5187 serves local working tree. API sources expose model/UVT/ЖДЯ records. Source snapshots and reproducible extractors retained here and in etl/. Product explanation docs/transport-network.md.

Final live verification through frontend5187 proxy saved in local-api-check.json:46487 links, Vladimir501rail/9air models, Yakutia2outgoing official rail chains. Desktop Chrome clean reload verified Vladimir map and unchecked model toggle count510. A transient Fast Refresh hook-order error cleared on full reload; no source change needed. No mobile checks. Context chronology moved to work/integration/session-before-network-local-20261110.md; all quoted instructions retained in protected section, budget passes.
