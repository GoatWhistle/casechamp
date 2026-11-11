# Chat workflow completion, 2026-11-11

## Scope and screen contract

Continue the last local Claude session `26df06b8-be6d-4a54-bab1-700e071972a6` on
`feat/map-first-ui`, starting at `4218fbf7a3b4d02052a6843fb28bfdf846b907d1`.
Preserve its pending removal of separate summary/scenario panels and move map work into chat.
The user subsequently requested provider authentication repair, semantic chat titles, subtle
assistant frames, removal of completed/action/source disclosures, a source follow-up, and
commits/push as Andrey. User-approved port is 8080; port8000 belongs to MASP/modus.

The right panel has one conversation. Selecting a region inserts a summary card. Selecting
roads prepares a closure question without overwriting manual text. Scenario/analysis results
remain inline, with explicit map actions. Assistant text uses existing muted-surface and border
tokens,16px padding and the existing large radius. Empty pending answers do not show a frame.

Pending responses retain their current-stage indicator. Completed responses have no status
label or tool-action disclosure. A completed answer offers “Покажи источники”; the action sends
an ordinary user question with history. Links and metadata remain visible in the returned
answer. The suggestion is absent during streaming, errors, region-only cards and immediately
after a source request. The source URLs of displayed tables are carried in history.

Generated titles arrive as metadata in the existing stream, remain attached to the originating
session during parallel chats, and persist in localStorage. Only the first question can request
a title. Untitled older chats keep the first-question fallback; source follow-ups cannot rename it.

Desktop widths1440/1920 are the acceptance viewports. No mobile checks by standing user request.
Existing motion tokens and reduced-motion handling are retained; no new animation is introduced.

## Implementation

- Fixed the unfinished analysis-table header type, split analysis results to satisfy complexity
  limits, and retained keyboard-safe map focus. Removed orphaned UI and imports with the deleted
  scenario panels. Regenerated the full current OpenAPI document and frontend types.
- Selected-road context validates at most50 positive OSM way IDs with names up to200 characters.
  Region cards remain outside model history and survive a retry.
- `name_chat` validates one nonempty title up to80 characters. Gateway instructions request
  3–7 Russian words using the question and history, without echoing the naming operation.
- Removed `Ответ готов`, action lists and source/parameter disclosures. Explicit source requests
  preserve source paragraphs that ordinary presentation hides. Existing mathematical rendering,
  analysis tables, scenario cards and map actions remain available.

## Authentication evidence

The container could read the saved account. `account(refresh_token=False)` returned an account;
forcing refresh returned HTTP401 and cleared that process's cached account. The existing access
token was still valid, and an authenticated model-catalog request succeeded. No credentials or
tokens were printed. The gateway now reads the existing account without forcing refresh before
every question; the model provider retains its normal expiry-based refresh.

A regression first failed against the old behavior, then passed. The deployed gateway's auth
phase was exercised with its model runner replaced by a local completed event, without inference.
No live model answer or semantic-title quality evaluation was run in this task.

## Verification

| Check | Result and evidence |
| --- | --- |
| Frontend initial `npm run verify` | Passed:36 rules, TypeScript, Biome,426 tests, production build; `/tmp/casechamp-chat-final-verify.log` |
| Frontend final `npm run verify` | Passed:36 rules, TypeScript, Biome,427 tests/62 files, production build; `/tmp/casechamp-chat-followup-final-verify.log` |
| Backend Ruff/mypy | Passed;185 source files |
| Backend unit suite |257 passed after the title correction; `/tmp/casechamp-chat-followup-final-backend.log`; commit hook reruns required tests |
| API and storage smoke | Live health, regions and road viewport succeeded on8080; no schema/storage changes |
| Real road workflow | Passed: select a real road, prepare prompt, preserve manual draft on clear/reload, restore one region card, create another chat; `/tmp/casechamp-chat-browser.json` |
| Map interaction E2E |5/5 passed after correcting region hit readiness and isolating it from road selection; `/tmp/casechamp-chat-map-final-e2e.log` |
| Chat browser check | Passed with controlled NDJSON and live atlas API: frames, titles, source follow-up, reload/history; zero page/API errors and zero sidebar axe findings; `/tmp/casechamp-chat-ui.json` |
| Desktop visuals |1440/1920 screenshots inspected; `/tmp/casechamp-chat-ui-1440.png`, `/tmp/casechamp-chat-ui-1920.png` |
| Documentation | Relative-link check for chat/API/design decisions and `git diff --check` passed |

The existing build warns about large chunks and a PostCSS plugin missing `from`.
The initial map test passed4/5 cases: camera initialization did not establish a rendered region
hit, and visible roads can intercept a region click. The corrected test disables the road layer,
waits for a real region hover, then verifies selection and camera focus. A direct browser probe
selected Krasnoyarsk `04000000`; its zoom increased from2.121. The hidden switch input is covered
by its visible label, so the test clicks the label as a user would.

After reloading at1920px, road rendering did not finish within45 seconds;28 geometry parts were
already visible and chat restoration had succeeded. This is a remaining performance observation,
not an assertion that the whole road layer loaded within that deadline. The final chat visual
check waits for the region card and visible road parts; full road completion is covered separately
by the1440px selection check. No map rendering performance change was made in this task.

The first source-follow-up test needed the router and ResizeObserver test environment; final
verification passes. The first title schema used a default that the generator treated as required;
`default_factory=bool` preserves optional wire input and the false server default.

Impeccable's launcher could not create its cache under the sandbox; local product/token rules
were used. The UI/UX search data was absent. Playwright MCP lacked its expected Chrome binary;
the installed Playwright Chromium was used directly. A browser approval timed out once and the
same authorized local check succeeded on retry.

## Runtime and publication

`docker compose -p casechamp --env-file .env.analytics` uses the existing ignored local auth
override and persistent ClickHouse data. Rebuild backend/frontend, then `up -d --no-build`.
No tokens, local env files, auth override or browser histories belong in the commit.

All three Compose services are healthy on8080. The temporary Vite server on5179 was stopped.
Remote `origin/feat/map-first-ui` matched local HEAD before publication. Use command-scoped
author and committer `andreysk0304 <andreysk0304@yandex.ru>`, matching recent commits; preserve
the configured global/local identity. Final publication includes the corrections below.
The unrelated `/scenarios` matrix laboratory still lacks its `plexus_scenario` dataset.

## Follow-up corrections, 2026-11-12

The user observed a source request replacing an untitled conversation's heading, scrolling
being pulled downward, and white gaps while scrolling. Both behavioral regressions were first
reproduced by failing tests. The title flag was true on a follow-up when the initial response
had omitted `name_chat`; it is now limited to the first question on both client and server.
Unrequested title events are ignored. Existing saved headings are retained.

The browser baseline confirmed that a40px upward wheel movement was undone by the next text
chunk: scrollTop9159 →9119 →9215. The80px near-bottom threshold kept automatic following enabled.
Wheel, keyboard and pointer reading intent now interrupt following immediately; scrolling back
to the bottom restores it. The source-answer test asserts the reading position survives a chunk.

The baseline also confirmed an8072px-tall answer retained `blur(0px)` and an identity transform
after its entrance animation. The message now uses the existing opacity-only fade token, removing
the large filtered surface. Headless resting screenshots did not reproduce the reported white
gap; final checks inspect three positions in a long answer and verify no filter or transform.
No claim is made that a device-specific compositor issue was reproduced on the user's browser.

Baseline browser evidence: `/tmp/casechamp-scroll-before.json` and three scroll screenshots.
Final correction verification passed after deployment on8080. Browser evidence:
`/tmp/casechamp-scroll-after.json`. A source request carried `title_requested=false` and its
unsolicited title event was ignored. Reading position remained9119 before/after a streamed
fragment. Home kept the view at0 while more text arrived; End restored following. The8072px
answer had `filter:none` and `transform:none`. Screenshots at scrollTop1389,4630 and7871 were
inspected without white gaps. No page errors were reported. Model events were controlled test
streams; no live model inference was invoked by these checks.

One earlier full frontend run timed out in an unchanged analysis-commentary test at5 seconds;
the final full run passed427 tests. The source/scroll regression tests failed before their fixes
and passed afterward. Backend Ruff, mypy and257 unit tests passed; both application containers
were rebuilt and the Compose runtime is healthy. The temporary Vite server remains stopped.

The initial source commits5aa8d1b and0612343 were pushed successfully after one stalled HTTPS
attempt was interrupted and retried with a45-second limit. No history was rewritten.
Final product source checkpoint: `af825ca2b84e9a7d174bdb051c2fc2f385b93c82` on
`feat/map-first-ui`, including title correction088c141 and scroll/paint correctionaf825ca.
Both are authored and committed as Andrey. The publication target remains
`origin/feat/map-first-ui`; no implementation work remains after the verified deployment.
