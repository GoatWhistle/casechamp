## Current state

- Branch `feat/frontend`, HEAD `ca97c39`; implementation `96cd7b7`, audit `ca97c39` (base `a445fa8`). Approved root `index.html` and `tabs-updated.html` are integrated into native frontend components. API/backend unchanged; root HTML and other prototype-session changes excluded from implementation commit.
- Implemented: animated home at `/`, working atlas at `/map`, region compositions and seasonal comparison, source topic tabs, region profile/calendar, illustrative Hansen matrix. Existing settlement/financial screens retained through profile disclosure.
- Verification: 369 unit tests plus rules/typecheck/lint/build passed. Desktop widths 1280/1440/1920 only; seven screens at 1440 axe0. 17 desktop e2e passed; 21 final captures complete. Evidence/limits: `work/audits/prototype-integration/`; decisions: `docs/design-decisions.md`.
- Fixed during checks: table scroll trapping; stale season links on immediate navigation; delayed route focus interrupting search. DOM RouterProvider supports synchronous season updates.
- Unavailable API content deliberately omitted: MChS observations and source PDF URLs. Calendar distinguishes report date from unknown closure; regional index remains missing honestly.
- Publication uses the configured human Git author Ivan Gerasimov <ivandivan2909@gmail.com> per current AGENTS and authenticated GitHub `ivanGMAI`. Remote origin/feat/frontend was verified at `a445fa8` before publication; the latest user instruction authorizes committing and pushing the accumulated frontend work.
- Earlier details and exact session pointers: `work/audits/prototype-integration/session-before.md`; map performance: `work/map-performance/compositor.md`; prototype evidence: `work/design/home/README.md`, `work/design/tabs-update/README.md`.
- Pre-existing DESIGN.md/PRODUCT.md placeholders and Chukotka seam remain outside this transfer. Protected instruction overflow retained.

- Local preview: port 8080 belongs to Compose `app-frontend-1`, config `/tmp/plexus-map-compose.yml`. Frontend rebuilt successfully with `up -d --build --no-deps frontend`; backend container `app-backend-1` stays unchanged. Local preview ready at `http://localhost:8080`; no push performed. Next: user clicks through the preview and provides feedback.

- Home review follow-up: removed replay button, its handler/style and unused dictionary key; updated existing home e2e. Frontend-only preview on 8080 updated. Changes remain local; push still deferred.

- Review follow-up complete: restored pre-integration large MapExplorer at `/map` with original controls, metrics, overview/ranking and selection zoom. Home CTA uses `/map`; other redesigned tabs remain. No new commits.

- Latest checks: `npm run verify` passed (369 tests); 13 desktop e2e on production 8080 passed, including old map gestures and axe. No mobile checks. Review evidence: `work/audits/prototype-integration/review-followups.md`. HEAD still `ca97c39`; all feedback remains uncommitted for one later batch.

- Current feedback batch: source tab underline is local to the active label; method readout follows pointer hover and focus; settlement table permits document scrolling; selected map region replaces national ranking with API-backed settlement routes. Shared `LinkList` is reused in the profile. Four regressions failed before fixes and now pass on production 8080; npm run verify passed (372 tests), all 21 desktop e2e passed. Frontend-only 8080 rebuild complete. Four desktop screenshots reviewed; no horizontal overflow or axe findings. No mobile checks, commits or push. Next: user reviews localhost:8080; collect further feedback for one later commit.

- Publication in progress: stage frontend feedback, design decisions, context and review evidence only; leave unrelated prototype-session files and setup executable-bit changes local. Preserve all four root HTML files. Existing verification remains green (372 unit tests, 21 desktop e2e). Push the feedback commit together with `96cd7b7` and `ca97c39` to origin/feat/frontend.

- 2026-11-08 evening, HEAD `0fea833` pushed: `/` has no header; one wordmark with rings; map of real link endpoints from new `GET /api/v1/links` with a hub tour (lines to stations, one-shot ripples, label shows only the place name). 404 and failure words use outside-only rings from `work/brand/export_iso_text.py`; failure page is centered without buttons. `/map` ripples the selected region after the camera settles. Next: user review of the landing tour, 375 px check of `/`.

