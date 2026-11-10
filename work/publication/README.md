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

Pending: finish export, verify full remote asset manifest, publish release with restore
instructions, commit publication artifacts, update final context and push.
