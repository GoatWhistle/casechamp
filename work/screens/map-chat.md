# Map chat

Mode: Operate. Right sidebar beside the atlas, existing summary retained as a tab.
User asks about selected territory; server context includes region, season, network and metric.
Visual reference: GoatWhistle/rwb b24b3d5, chat screenshot and chat-panel/composer/message source.
Preserve Onest, light Plexus tokens, blue user bubbles, plain assistant prose, bottom rounded composer.
States: empty suggestions, connecting, tool action, text streaming, complete, canceled, safe error/retry.
Keyboard: Enter submits except IME; Shift+Enter newline; native buttons and existing Segmented/Disclosure.
No voice, mobile checks, invented metrics or scenario recalculation.
Structured tables and bar charts share tool data. Markdown lists/GFM tables and source disclosures follow rwb presentation rules.
Impeccable launcher unavailable (cache permission); direct project/reference reading used.
UI UX search data missing; existing project accessibility rules used instead.

## Verification, 2026-11-10

Branch feat/map-first-ui; base 63fb9cb44f4fe53ce16c7d64e571bca234fb0135.
Pydantic AI2.66.0 / openai-codex0.167.0 / gpt-6.1-sol through local ChatGPT authorization.
Actual Responses calls: selected Stavropol returns944 links; national ranking emits table/chart
and text deltas, with coverage caveats. Five-region result: Chukotka0.151, Nenets0.581,
Magadan2.336, Yamal-Nenets3.573, Sakhalin3.842. These are atlas values, not a fresh model calculation.
Second browser request exercised a three-region chart and numbered conclusions.
Desktop1440x1000 and1920x1080: no page errors, document overflow or axe violations.
Screenshots: /private/tmp/plexus-chat-artifacts-final-{1440,1920}.png.
Earlier browser checks passed cancellation, clear conversation, summary switching and long prompt.
No mobile checks per active user instruction.

Frontend: TypeScript,36 rules,364 tests and production build passed. Full verify stops on
pre-existing import ordering in tests/entities/region/boundary-geojson.test.ts; changed files lint clean.
Build warnings: existing large map chunk and PostCSS missing from option.
Backend: ruff/mypy passed;7 targeted chat/artifact tests passed; full unit suite142 passed/5 failed.
The five failures predate chat and encode older data counts: totals1650 vs12391, Altai8 vs239,
coordinate routes maximum997 vs11677, Stavropol653 vs944 and repository1650 vs12391.
No storage changes or integration suite. No commit, push or deployment.
Local frontend5187 proxies backend8001. Default CHAT_ENABLED remains false elsewhere.

## Map control and math, 2026-11-10

Added control_map tool with validated atlas region IDs; map stream events, replay buttons,
single/group selection, one-step zoom and country reset. Geometry and camera never come from LLM
coordinates. Math normalization supports dollar/TeX/legacy parenthesis forms; KaTeX0.19.1 pinned
through overrides for remark dependencies; native MathML output, trust false, maxExpand1000.

Final checks: frontend369 tests,36 rules,TypeScript and build passed. Full verify remains blocked
only by existing boundary-geojson.test.ts import ordering. Backend ruff/mypy passed; targeted
chat/map/artifacts/architecture25 passed; full unit143 passed/5 prior dataset-count failures.
Live Codex browser: Tyva93000000 focus zoom5.960, group with Altai84000000 zoom5.411;
one-step zoom5.960→6.960; reset country zoom2.329. Pointer interruption stopped at zoom3.373,
center82.945,59.129 and stayed unchanged1100ms later. Reduced-motion replay/reset reached final
views within100ms. Zero JS errors,axe violations,document overflow. Screenshots inspected at
1440/1920: /private/tmp/plexus-map-agent-formula-1440.png and plexus-map-agent-group-1920.png.
First live automation was interrupted by Vite HMR during editing; repeated on stable source.

Motion review: occasional geographic focus preserves spatial continuity with MapLibre's camera
flight, curve1.25,900ms --dur-map; ordinary step zoom260ms. New flights and native drag interrupt
rather than queue; reduced motion skips movement. No per-frame React updates, pitch or rotation.
The900ms map duration uses the repository's existing rare-event exception. Review approved for
this spatial transition; no new UI entrance/exit animation. Stale cached region label after group
selection was corrected to derive from current context rather than prior query data.

## Corridor calculation visual, 2026-11-10

Chat closure emits typed calculation event with full corridor geometry and both jobs.
Inline SVG reflects actual geometry, shimmer only while queued/running, per-region polling,
server progress, completed before/after/delta, failures and retry. Map closure dashed red;
initial fit once, explicit refocus button, reduced-motion and keyboard instant refocus.
No paid model call. Browser harness uses real saved corridor with test statuses/results;
these screenshots are UI checks, not calculation evidence. Existing messages need new turn.
Frontend verify 381 tests, backend focused26/Ruff/mypy pass before final copy/refocus tweak.
Screens /tmp/chat-calculation-1440.png and /tmp/chat-calculation-1920.png.
Final verification after copy/refocus change: frontend verify381tests/build passed;
browser1440/1920 waiting-to-completed transition, map corridor ID, reduced motion,
JSerrors0 and axeviolations0. UI test values are synthetic; no paid model call.
Context compact-context: three paragraphs moved to work/integration/session-before-chat-visual-closeout.md;
protected quotes preserved; budget check passes with protected-text notice (SESSION12622chars).


## Starter examples, 2026-11-12

Replaced only three starter strings in frontend/src/shared/i18n/locales/ru/chat.json:
road improvement priorities, closure consequences and adding a road between cities.
Branch feat/transport-scenarios-update, HEAD986ae0f5ee754b9e98f25e2e608b5bc37cbad507.
Dictionary Biome and frontend build pass; verify stops on pre-existing css-literals/css-duplicates in traffic UI.
Browser QA blocked: sandbox Chromium launch denied; CUA has no available browsers.
No commit/push/paid calls. Preserve unrelated work; review in existing local UI5187.


## Thinking indicator, 2026-11-12

Requested: three dots exchanging positions while the model is working. Shared ThinkingDots
replaces the idle glyph only while the current conversation is busy, including further model
work after tool artifacts arrive. Completion, cancellation and failure unmount the indicator.
The existing status remains a live region; the three decorative dots are aria-hidden.

Predetermined CSS transforms and opacity use the existing motion tokens. The 1.56s loop
represents ongoing work; each half-step uses the existing 260ms panel duration. It starts
with the existing 400ms spinner delay and 160ms fade. Reduced motion keeps each dot in its
own position and substitutes a 1.6s opacity pulse. No new dependencies or paid calls.

Motion review against review-animations/STANDARDS.md:

| Before | After | Why |
| --- | --- | --- |
| Static busy glyph | Three phase-shifted dots | Indicates work without moving content or blocking input |
| Busy status hidden when results arrive | Busy status stays until model completion | Tool results can precede further model work |
| Spatial movement | Fixed positions with opacity in reduced motion | Keeps feedback without positional movement |

Approve: transform/opacity only, token timing, immediate unmount, fixed footprint and
reduced-motion variant. Existing shared animation standards pass.

Verified 2026-11-12: npm run verify passes all 36 rules, typecheck, lint, 491 tests and build.
Additional focused run: 57 tests across 18 files passed. Chromium checks at desktop1440/1920
cover all three dots, normal/reduced motion, completion and cancellation. Test-only intercepted
chat responses; no real model call. Captures and six phase frames: /private/tmp/plexus-thinking/.
Branch feat/transport-scenarios-update, HEAD986ae0f5ee754b9e98f25e2e608b5bc37cbad507.
Unrelated dirty work preserved; no commit/push/restart. No mobile checks per user instruction.
