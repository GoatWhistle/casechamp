# Frontend upstream integration, 2026-11-11

Current branch: feat/map-first-ui, HEAD cdb2c2e.
Fetched origin/feat/map-first-ui at 5cd8921.
Relevant upstream commits: 898a25d (scenario event contract), 78fdc0a (map screen redesign), 5cd8921 (design notes).

Applied frontend changes as working-tree integration, without moving HEAD, committing,
or modifying backend/data. Local uncommitted implementation retained. Pre-integration
source backup: /tmp/frontend-sync/local-src. Upstream patch and check logs:
/tmp/frontend-sync/.

Conflicting chat shell, calculation rendering, legend and scenario forms retain local
behavior (floating chat, result commentary, settlement focus, appraisal and stress tests).
Other upstream panels, transport visualization, primitives, typography, summaries and
comparison screens integrated. Scenario SSE parsing/rendering supports the upstream
contract, but the current backend was not changed to emit new scenario events.
This is an adapted integration, not a full fast-forward or an identical upstream UI.

Initial verification exposed merge/API issues, obsolete dictionary keys and changed
flight geometry assertions. Build and 466 tests passed after fixes. Final verify log:
/tmp/frontend-sync/verify-final.log. No browser visual verification yet; no paid calls.

Final validation: all 36 repository rules pass, TypeScript passes, Biome reports no
errors (one pre-existing informational template-string suggestion), 466/466 tests pass.
