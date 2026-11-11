# Minimal calculation chat, 2026-11-11

User requests: compact animated background progress instead of job-ID tables; automatic
human interpretation when done; no nested cards, repeated map previews, road-name inventories
or unnecessary disclosures. Exactly one selected-section map at the beginning of the message.
The user clarified this means the chat UI, not a Markdown file. No mobile checks.

Implemented: ChatAnswer renders one section map before prose; all scenario/stress jobs in the
answer share one thin progress bar. Known progress uses saved completed/total counters;
national stages have their own counters, not a guessed ETA. Queue/unknown progress uses a
subtle opacity pulse. The bar animates transform200ms; reduced motion disables movement.
Calculation ID tables and scheduling boilerplate are removed only when backed by structured
artifacts. Technical job IDs remain in history for follow-up tools. No outcome data fabricated.

After all jobs reach a terminal state and at least one succeeds, the UI asks the dedicated
POST /api/v1/chat/calculation-review endpoint. The server loads saved results, replaces client
claims/history and supplies concise interpretation rules. Review calls expose no tools.
Partial failures remain explicit. All-failed/cancelled groups never call the model.

One commentary per result revision is shared by QueryClient. Started commentary continues
when its component unmounts and writes back to the originating conversation. Completed text
survives reload. Interrupted browser sessions retain partial text and expose manual Retry;
there is no blind automatic retry. New pending jobs remain marked in session storage.
Historical completed messages do not launch reviews simply because they are rendered.
The latest legacy answer can request its missing review. Route-only artifacts keep the main
agent's immediate route explanation instead of adding a new national-impact review.
Numeric jobs keep running server-side; an unmounted pending conversation is checked again
when opened. There are no background browser push notifications.

Validation: backend Ruff check/mypy269files,387unit tests and47real ClickHouse integration
passed. Frontend verify466tests passed; final narrow follow-up verification recorded below.
Desktop Playwright uses real saved714-way geometry/totals and controlled progress states.
Only the model response is intercepted in the browser test to avoid paid calls; no paid semantic
model evaluation was performed. It verifies one leading map, counter25%, ID-table suppression,
automatic single request, readable Markdown, reload without repetition and axe accessibility.
Browser screenshots: browser-check/. Real user four-region jobs read from main API are in
saved-jobs.json, all completed. Backend tests independently prove authoritative saved data,
all-jobs readiness, unavailable-result guards and no fallback to an ordinary tool-enabled turn.

Runtime: main API8007 was restarted by a concurrent task (PID31326), and its OpenAPI confirms
the review route. Primary UI5187 has current source. Owned preview5190 now proxies API8007;
API8817 remains the older separate validation process. No commit/push/deployment.
Shared uncommitted work preserved. A parallel regional-consequences change briefly had import
ordering failures; latest global Ruff passes. New module/test Ruff-format passed; global
format baseline remains previously recorded in work/road-stress/compact-ui.md. Build retains
existing PostCSS/chunk-size warnings. Initial cwd mistakes and type/complexity checks were
fixed before passing verification.

Final verification: frontend verify466tests passed after the history-review guard and removal
of the premature global "answer ready" status. Final desktop scenario (browser-final/) passed in5.1s on rerun
with the updated primary API proxy. The first attempt stopped before UI loading because
the saved-job API response was non-2xx; a later read confirmed200 on8007 and5190.
Both final1440px screenshots were visually inspected: one leading geometry preview,
minimal progress and plain Markdown interpretation, without repeated cards. API8007 exposes the dedicated review route; the primary
process was updated concurrently, not killed by this task. Model generation was still mocked
only in UI tests; no paid call was executed by this task.

Closeout context check passed: README4034, SESSION20026 (mutable4778), openquestions1418
characters. A concurrent session moved prior details to work/chat-debug/context-before-compaction.md;
this task made no additional context deletions. Protected instructions remain verbatim.

## Tool-result prose follow-up, 2026-11-11

User: «почему тут все равно 100500 вложенностей».
The remaining nesting came from ChatArtifacts wrapping tool tables in Card and DataTable,
independently of the already simplified calculation renderer. Removed both wrappers from
all tool-result types in chat. Connectivity becomes Markdown with a route heading, before/after
hours, score/change and model notes. Adjacent summary/pair artifacts share one prose block;
a single pair does not repeat its score. Identical city/region labels are deduplicated.
Missing scores remain explicitly unavailable, unbound/unreachable states remain distinct,
and real zero scores remain visible. Other tool tables use Markdown lists with all columns;
charts and source links stay available. Large lists retain the existing show-all control.
Existing saved messages use the new renderer; stored artifacts/history/contracts are unchanged.

Desktop browser inspection: artifact-saved-message.png and artifact-missing-message.png,
plus full1440px captures. check-artifacts.cjs uses the saved real capital-pair result from
work/chat-debug/pair-validation.json and a labelled missing-result edge case in an isolated
browser context. Both had zero bordered descendants, no HTML table, no page error and no
paid model call. Existing connectivity tests3passed; changed-file Biome passed.
First aggregate verify/typecheck attempts intersected concurrent frontend restructuring;
all own TypeScript errors were fixed. Early Biome cwd and edit cwd mistakes made no edits.
Final aggregate verification status is recorded below after completion.

Final frontend npm run verify exited0: repository rules, TypeScript, Biome, unit tests
and production build passed. Existing informational Biome/PostCSS/bundle warnings remain.
Both browser screenshots were inspected. No API restart, commit, push or deployment.
