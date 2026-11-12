# Worktree consolidation, 2026-11-12

Target: feat/map-first-ui, base 8d62824, origin/feat/map-first-ui initially identical.
All five additional worktree branches point to 0c7cb89, already an ancestor of target.
Their uncommitted tracked and untracked files were consolidated into the target.
Source worktrees remain intact. Context snapshots and differing research versions are
preserved under work/worktree-snapshots/. Existing main-branch research variants
are preserved in main-before-consolidation. No root HTML added.

## Validation

- Frontend npm run verify: passed, 36 rules, typecheck, lint, 462 tests and build.
- Backend Ruff and mypy: passed, 332 source files checked by mypy.
- Backend unit tests: 629 passed.
- Integration first run lacked ClickHouse environment variables.
- Integration rerun with .env.analytics: 57 passed, 2 failed; interrupted after
  100 seconds while waiting for storage. Failures: empty saved analysis list in
  test_saved_analysis_details_remain_readable; HTTP 503 data_unavailable in
  test_api_selects_exported_scenario_and_coverage[all-road-road]. Full suite incomplete.
- Context budget permits SESSION overflow for protected user instructions.
- Browser checks not performed for this consolidation.

Publication: commit to feat/map-first-ui and push to origin, authorized by user.
Command-scoped author and committer: andreysk0304 <andreysk0304@yandex.ru>.
