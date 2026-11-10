# Publication, 2026-11-10

User requested all changes committed/pushed and data published. Explicit confirmation
covers six dataset databases in private GoatWhistle/casechamp release data-clickhouse-20261110.
User calculation history plexus_state and credentials are excluded. Root HTML stays local.

Code: 20feac3 captures the initial working changes; 6ca0e3e merges seven remote commits.
Push to origin/feat/map-first-ui succeeded without force. The remote scenario model needs
point_index; the ClickHouse adapter has no point IDs in its empty scenario dataset, so it
supplies an empty mapping. This limitation is recorded in docs/design-decisions.md.

Checks before merge: frontend verify, 411 tests; backend Ruff/mypy, 163 unit, 40 integration.
Checks after merge: frontend verify, 411 tests; backend 167 unit, 40 integration; mypy for
tracked files passes. An isolated archive of commit 6ca0e3e also passes Ruff and mypy
(151 source files), excluding concurrent work. A simultaneous accessibility implementation created new untracked
files and later edits main.py; these are outside the published checkpoint and remain intact.
The earlier mypy/Ruff failures in accessibility.py belong to that in-progress work.

Fixed existing failure test_completed_calculation_survives_storage_timeout: DataUnavailable
while saving a completed job retains the result in memory with storage_pending; it logs the
storage failure separately. This does not implement persistence retries or restart recovery.

Data: export_snapshot.py reads table-by-table using Native+gzip. Upload checks GitHub asset
size and SHA-256 before removing only the generated local compressed copy. The manifest
records schemas, row counts, timestamps and hashes. Export can resume and retry TLS failures.
The unfinished plexus_refresh_graph is separately labelled staging and excluded from default
restore. Native state/system databases are never exported. The six database names are fixed.

Restore smoke: downloaded plexus_additional.dim_region from the draft release, checked hash,
restored into publication_verify_additional, compared all 82 rows to the source, then removed
only that scratch database. Full clean-server restore has not been run.

Context compaction: the former state is preserved in session-before-publication.md. All user
quotes remain verbatim in context/SESSION.md. Its protected section exceeds 6000 characters;
mutable state is within the budget. No historical entry was discarded from the archive.

Final release: https://github.com/GoatWhistle/casechamp/releases/tag/data-clickhouse-20261110
87 tables, seven databases, 184,716,898 table rows (not unique entities), 2,757,503,413 bytes.
All GitHub asset sizes and SHA-256 match. The combined manifest and SHA256SUMS accompany
the data; a copy is in docs/results/clickhouse-release-manifest.json. Root passport PDF
and all current concurrent changes are included in the closeout commit. Road refresh remains
staging. No deployment or activation of the unfinished refreshed graph occurred.

## Final working-tree checks

At 20:49 UTC: Ruff/mypy pass (165 source files), 195 backend unit tests pass; frontend
verify passes with 415 tests. Integration: 41 pass, 2 fail in test_accessibility_storage.py
because plexus_accessibility.runs does not exist yet. The separate potential calculation
is still running; do not synthesize data or hide these acceptance failures. The release
exports only the six explicitly approved dataset databases and preserves the active model.
All current code changes are being captured, including completed corridor fixes and the
new comparison UI with its honest unavailable-data state. New comparison data are not
part of the six-database snapshot.

## Resolved checks and additional data

At 20:57 UTC both previously failing integration tests passed on rerun after the potential
calculation finished. The parallel full integration log records 43 passes. The user explicitly
approved adding plexus_accessibility.runs, results and frequencies to the same release.
Three extra tables (1, 492 and 12 rows) are uploaded with verified SHA-256. On 11 November
Moscow time, five downloaded tables were restored to isolated scratch databases and compared
row-for-row: all 587 rows equal, including an empty scenario catalog. Scratch databases were
removed; no active data were changed. Evidence: restore-verification.json.
