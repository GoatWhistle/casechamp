# Legend and chat upstream integration, 2026-11-12

Branch feat/transport-scenarios-update; base HEAD986ae0f5ee754b9e98f25e2e608b5bc37cbad507.
No commit or push. Prior road-analysis changes and concurrent research/ETL work retained.
Earlier comparison: [remote integration check](../remote-integration-check-2026-11-12.md).

Imported legend implementation from4218fbf (includes87c2398 and8e795a3): persistent
width/height, lower-left anchor, diagonal resize, border resize, collapse/reopen,
keyboard controls, focus return, blocked-storage handling and reduced motion.
Shared width/resizer extensions retain existing sidebar defaults.

Imported initial-question naming from0612343/088c141 without their unrelated chat
restructuring. NDJSON title events and optional title_requested pass through the real
API and saved-session validation. The naming tool is registered only for an initial
non-review request and passes the existing skill-tool filter; it disappears after
naming. Later questions, reviews and unsolicited replacement titles cannot rename a chat.
Old sessions keep the first-question fallback. No paid model calls were made.

Imported af825ca scroll hook and opacity-only message entry. Regression command:
`cd frontend && npx vitest run tests/features/map-chat/chat-scroll.test.tsx`.
Before: small upward scroll to560 was overwritten to1000 on the next text delta.
After: position remains560; scrolling back to the bottom restores following.
Initial test harness lacked ResizeObserver; stub added before the actual red reproduction.

Checks:
- Frontend npm run verify passed:36 rules, TypeScript, Biome,483 tests and build.
- Backend Ruff and mypy passed;417 unit tests passed. Title tests cover normalization,
  first-question eligibility, protocol/filter behavior and suppression during reviews.
- Six real-browser legend tests passed on API8007/UI5187, including pointer/keyboard,
  persistence, cancellation, limits and reduced motion. One reading/title browser test
  passed with a test-only saved conversation; no paid request. Axe found zero violations
  in legend/chat surfaces. Screenshot inspected.
- API8007 restarted idle fromPID24793 toPID44106 with the same GRAPH_DIR=data,
  CHAT_ENABLED=true and ROAD_WORKERS=6. Analysis/scenario/stress recent lists contained
  no active jobs before restart. Live OpenAPI confirms title flag and event. Log:
  /tmp/plexus-legend-chat-api.log. Frontend PID59324 unchanged and hot reloaded.

Limitations and corrected checks:
- No live paid title-generation run; provider behavior is covered with local test models.
- No new storage changes; integration suite not rerun for these UI/chat-contract changes.
- Full backend ruff format check reported83 unformatted files; newly added
  title-test file subsequently formatted. Existing files were not reformatted wholesale.
- API types command initially failed on registry DNS. Generated from backend/openapi.json
  using cached official openapi-typescript7.13.0. Optional title flag is derived from
  generated types at the input boundary and defaults tofalse before the API call.
- First frontend verification preceded regeneration, then exposed defaulted input typing;
  both corrected before the successful final verify. Existing PostCSS/from and bundle
  size advisories remain. Impeccable launcher cache permissions unavailable; incumbent
  PRODUCT.md/DESIGN.md, tokens and direct craft-floor/UI guidance used. No mobile check.

## Motion review

| Before | After | Why |
| --- | --- | --- |
| Message entry shifts text | Existing fade token | Preserve the reading position |
| Legend fixed on screen | Anchored pop, faster exit, immediate keyboard toggle | Follow the originating control |
| Pointer resize | Direct size preview, no layout transition | Avoid lag during dragging |

Approve: transitions interrupt correctly, reduced motion is respected, no new literal
durations or layout-property animations. Relevant sources: legend/legend-panel.tsx,
legend/legend-panel.module.css, scroll/use-chat-scroll.ts and chat-message.module.css.
