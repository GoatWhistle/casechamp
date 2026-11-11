## Concrete regional consequences, 2026-11-11

Implemented regional delay exposure, lost nearby links, before/after times and named
connections in existing summary/agent tools; legacy calculation transfer and exact
saved-impact enrichment for automatic replies. [Evidence](../work/regional-consequences/README.md).
feat/map-first-ui HEADcdb2c2e.391unit/47integration/464frontend passed; two-region API
and independent aggregates verified. Main8007 PID34705 health and regional summary verified;8817 untouched.
No paid calls. Fixed weights/no queues; residents are exposure, not users or GDP.

## Frontend upstream integration, 2026-11-11

> посмотри последние коммиты фронтенда в репе и забери от туда его в нашу ветку текущую и текущую реализацию

feat/map-first-ui HEAD cdb2c2e; fetched upstream 5cd8921. Adapted frontend working-tree
integration retains local floating chat/appraisal/stress behavior; no backend/data changes,
commit or push. [Scope, source backup, checks and limits](../work/frontend-upstream-sync/README.md).

## Exact upstream frontend replacement, 2026-11-11

> прям весь фронт забрал ? там точно чат не такой
> забирай вообще весь

Supersedes adapted integration above. Replaced all frontend tracked/nonignored source
with origin/feat/map-first-ui 5cd8921fb7b51e302d29a0cdd36deb6387611e00.
724 files byte-equal, no extra/missing files. Branch feat/map-first-ui HEAD cdb2c2e;
no commit/push. Backup /tmp/frontend-full-backup-20261111-201838.tar.gz.
Backend/data unchanged. Remote UI intentionally replaces local floating chat, stress
and appraisal UI additions. Rules/typecheck pass; upstream lint formatting error in
frontend/tests/entities/road-graph/link-changes.test.tsx prevents full verify.
Separate test/build logs: /tmp/frontend-full-tests.log, /tmp/frontend-full-build.log.

Final exact-copy checks: build passes, 36 rules pass, typecheck passes. Upstream
lint formatting error remains unchanged; 434/435 tests pass, transit-geojson airport
anchor test expects a straight two-point line while upstream now draws a curved line.
No source fixes applied: exact upstream frontend requested and retained. Browser not checked.
