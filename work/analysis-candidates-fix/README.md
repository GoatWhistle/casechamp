# Regional candidate query repair, 2026-11-12

Branch feat/transport-scenarios-update, base986ae0f5ee754b9e98f25e2e608b5bc37cbad507.
Exact reported Saratov job: fb2880ec02634e53a2e2c0f091610cae.
ClickHouse candidates query reproduces HTTP500 with 30000 IDs:
HTML Form Exception: Field value too long. The same integration regression failed
before the fix and passed after it. Candidate reads now use 5000-ID batches,
deduplicating IDs before splitting and preserving all candidates.

Live retry uncovered an additional compatibility issue: boundary integer coordinates
become floats through storage; hashing raw JSON changed the fingerprint. Added a
failing numeric-roundtrip regression, normalized fingerprint coordinates, and excluded
incompatible saved jobs from submit deduplication. Old results remain readable.

UI distinguishes failed-empty from partial results in chat and analysis panel.
Regression confirms no saved-results promise and no model commentary for empty failure.

Checks: Ruff and mypy passed; 407 backend unit tests; 49 integration tests before
fingerprint change; frontend verify passed, 480 tests. Only touched Python files
formatted. Existing PostCSS/from and chunk-size warnings remain. No paid model calls,
no new browser visual check, no commit/push. API8007 restarted idle, PID24793;
log /tmp/plexus-analysis-fix-api.log. Original background start exited with shell;
detached restart succeeded. Early mypy/list type and frontend complexity errors fixed.

Live replacement Saratov +20% job f67252e917504d96b8d7db3b551ce9a8:
see live-result.json for latest state. Old chat points to the original failed job;
repeat the request to obtain the compatible replacement.
