## Current audit, 2026-11-12

Branch fix/desktop-scenario-audit, isolated worktree /private/tmp/plexus-desktop-audit; starting HEAD5daf6815eac9105d5b4b74e7013a5a49a5faf2e3.
User authorized real product requests through PC use and previously commit/push all.
Desktop Chrome scenarios: route, street closure, local improvements, three-city pairs,
national screening. [Findings, exact jobs, checks and unfinished UI retry](../work/audits/frontend-1.md).
Fixed route auto-map, connected named-street resolution,150km scope guard, independent
numeric-ID query batching, max_projects selection after local comparison, convergence
validation, compact agent payload/precision, negative delta sign and disclosure of atlas
selection tables. Saved conflicting closure now terminal-fails without changing raw history.
Verified451backendunit/50integration/500frontend; Ruff/mypy and full frontend verify pass.
API8007/8817 active from current source. Latest UI retry blocked by gray PC capture and
unreliable input; asked user to restore visible screen. No sent duplicate retry confirmed.
Ekb saved-input full replay completed; no stored result overwritten. National3-zone
UI run selected correct urban scopes, Ufa completed; dense-ID failures diagnosed/fixed.
Do not claim all3zones passed UI after latest fixes. Preserve unrelated new_math_core.md.
Prior implementation afd1d975 and closeout5daf681 pushed; current audit changes not yet pushed.
Before stopping: commit/push final audit evidence and record resulting SHA.
Concurrent external core edits appeared in the original tree during final review and
removed/replaced audited files. Do not commit or reset those changes. Audit source was
isolated from HEAD5daf681, retaining only diagnosed fixes and original contracts.
All checks are rerun in the isolated tree with its own etl/src on PYTHONPATH.
Protected user instructions exceed SESSION budget and remain verbatim.



## Isolated verification and source checkpoint

Implementation c59121a committed on fix/desktop-scenario-audit.
Ruff and mypy pass;451backendunit/50integration/500frontend tests pass in the
isolated tree. Frontend full verify/build pass with existing PostCSS/chunk warnings.
Pre-commit repeated451unit tests successfully. Credential-pattern scan clean.
No unrelated core code or new_math_core.md included. No merge into the concurrently
edited feat/transport-scenarios-update branch; conflicts need deliberate integration.
The test-only original-UI draft was not confirmed submitted. Full national3-success
UI result remains unverified; do not present local test coverage as proof of it.

Remote origin/fix/desktop-scenario-audit equals c59121a998a6118396085199a3fdd0755377359a.
The final documentation checkpoint may be a later subject-only commit on that branch.

Saved-input Ekaterinburg full replay completed (baseline/index/projects/index_comparing).
Log: ekaterinburg-replay.log. No active audit computation remains.

Final docs checkpoint6c5d459 pushed; original tree remains on feat/transport-scenarios-update.
Use /private/tmp/plexus-desktop-audit to inspect the verified branch. Do not reset original edits.
