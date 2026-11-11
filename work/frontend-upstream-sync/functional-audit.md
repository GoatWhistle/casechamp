# Functional audit after exact frontend replacement

2026-11-11; feat/map-first-ui HEAD cdb2c2e. Compared exact upstream frontend
5cd8921 with /tmp/frontend-sync/local-src (pre-integration source).

Confirmed regressions from source comparison:
- chat-stream rejects stress_test events and no longer dispatches calculation_review
  to /api/v1/chat/calculation-review. New backend output can terminate chat parsing.
- chat-map rejects focus_settlement. Settlement focus hook is absent.
- chat-artifacts rejects connectivity and connectivity_summary table titles.
- use-road-layer lacks stress region/point/route layers and their click handling.
- Road scenario lacks profile (lanes, highway, surface, speed) payload and appraisal UI.
- Local calculation progress/review hooks and result commentary behavior are absent.
- Saved chats with focus_settlement commands or connectivity tables can fail validation;
  stored browser records were not deliberately deleted. Do not clear local storage.

Preserved: road chunk loading, scheduling between parts, abort handling, selection,
base road geometry and API queries. Upstream adds major-road-first ordering, zoom-aware
paint and geometry simplification. Ferry-specific paint differs. These rendering differences
are not evidence of backend graph/data loss. Backend, ClickHouse, computed indices and
saved server-side jobs were untouched by frontend replacement.

Import incident: existing Vite PID8599 on5187 returned500 for router and map-page while
files existed and build passed. Restarted only this process, new PID59324 with API8007.
Router, map-page and proxied health returned200 after restart. Source unchanged.
The functional regressions above are diagnosed, not yet repaired.
