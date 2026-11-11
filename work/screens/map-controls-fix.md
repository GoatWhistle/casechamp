# Map legend and source tabs

Mode: Operate. Existing Plexus tokens and components remain the visual authority.

- Source tabs keep an underline on the selected tab. The previously documented behavior
  regressed when a full-width, clipped animated indicator was reintroduced. Existing
  `review-feedback.spec.ts` reproduces the failure on the published build.
- The lower-left map legend can collapse into a circular Layers2 button. Its colors,
  symbols and layer switches remain available when expanded. The icon denotes the map
  layers controlled by the panel, with a named button and tooltip.
- Drag the right edge to resize from 240 to 480px, starting at 320px. Arrow keys, Home/End,
  Shift with arrows and double-click reset use the shared resizer. Width and collapsed
  state persist locally; denied storage still permits the current interaction.
- Opening/closing returns focus to the corresponding control. Keyboard actions are
  immediate. Pointer toggles use the existing short opacity/scale transitions anchored
  at the lower-left corner, with faster exit and reduced motion. Dragging has no tween.
- Verify the source-tab regression and legend interactions against the real API at desktop
  widths only. Include narrow/wide legend content, rapid toggles, saved state, blocked
  storage, sidebar resizing and reduced motion. No changes to calculations or chat.

Tooling: Impeccable context loader could not write its engine cache. PRODUCT.md and DESIGN.md
remain templates; current tokens and rendered components are the operative visual reference.
UI/UX search data is missing, so accessibility guidance comes from the repository rules.

## Verification, 2026-11-11

- The existing source-tab test failed against the original build on port 8080: the
  selected tab started a clip-path animation on a span spanning the whole row.
- Four Chromium tests pass against port 8081 and the real backend: the original source-tab
  regression plus three legend scenarios. The first legend run found the splitter hit area
  covering the collapse button. Moving its top below the caption fixed the failure.
- Manual browser checks at 1440x1000 and 1920x1080 cover 240/320/480px widths, the round
  launcher and interrupted pointer toggles. No page errors; axe reports zero violations
  inside the legend. Mobile checks were excluded by the user's standing instruction.
- Artifacts: `/tmp/casechamp-ui-fix/{e2e-final.log,visual.json,legend-*.png,sources-after-1920.png}`.
  Screenshots show desktop geometry; the sources screenshot was captured during content loading.
- Baseline test repairs: the model-flight assertion now checks assigned airport endpoints
  and a curved path; the link-change assertion follows the existing formatter.
- `npm run verify` passes: 36 rule checks, TypeScript, Biome, all 435 unit tests in 64 files
  and the production build. The existing build warning for chunks over 500 kB remains.
- Rebuilt only the frontend through Compose. The production smoke check on port 8080 passes
  resize/collapse/reopen and source-tab selection without page errors. All three services are
  healthy. The temporary Vite server on port 8081 was stopped after verification.

Motion review: ready. Pointer toggles animate opacity and transform using existing tokens;
the exit is shorter. CSS transitions reverse from the current state after interruption.
Resizing follows pointer input without a tween. Keyboard toggles have no animation and focus
returns to a visible control. Reduced motion and denied storage pass browser tests. The launcher
stays anchored at the legend's lower-left corner. Source tabs have no moving full-row indicator.

The resize control uses the [WAI-ARIA window splitter pattern](https://www.w3.org/WAI/ARIA/apg/patterns/windowsplitter/).
Entry transitions use [CSS @starting-style](https://developer.mozilla.org/en-US/docs/Web/CSS/Reference/At-rules/@starting-style).

## Corner resizing

The user clarified that diagonal movement means resizing both dimensions, including shrinking.
The upper-right handle changes width and height together; the lower-left anchor stays fixed.
Dragging up/right expands, down/left contracts. Minimum size is 240x160px; width stops at 480px
and height stays within the viewport. Short panels scroll their content, leaving the caption
and controls reachable. Width and height persist across collapse and reload. Arrow keys resize,
Shift increases the step, Home/double-click restore automatic height and the default width,
and Escape cancels a drag. No tween while resizing. Existing right-edge width control remains.

The splitter shares the content grid row so wrapped captions cannot overlap it. The symbol key
switches to one column when the available width cannot fit two readable text columns, including
large-text settings. No synthetic data or development controls are added to the product.

Verified: six Chromium scenarios pass, covering growth and shrinkage, the fixed lower-left
anchor, 240x160px content scrolling, persistence, keyboard controls, reset, cancellation,
viewport limits, reduced motion and blocked storage. The first run used exact fractional
auto-height expectations; assertions now account for rounding to whole CSS pixels during
resizing. Visual checks at 1440 and 1920px and the legend axe check pass without page errors.
Growing the panel preserves content spacing; unused room stays below the content.
Evidence: `/tmp/casechamp-ui-fix/corner-{e2e-final.log,visual.json,*.png}`.

Motion review: resizing applies dimensions once per animation frame without transitions;
the existing collapse animation and focus restoration remain. No new animation or library.

Final `npm run verify` passes (435 tests, all rules, types, lint and build). The final Docker
image is running on port 8080; its ID matches the built image. A browser check against 8080
confirms the corner control, mouse enlargement and keyboard shrinkage. Screenshot:
`/tmp/casechamp-ui-fix/corner-production.png`. The existing bundle-size warning remains.

## Border interaction

The next request removes the visible corner button and the dark collapse tooltip. Resize
now starts from the transparent upper-right hit area or the existing right edge. The cursor
indicates the available direction. The corner retains its accessible name, keyboard controls,
44px hit area and screen-reader-only instructions. Its hit area is offset slightly outside the
panel to keep the collapse button reachable. The permanent right-edge grip is removed.
Collapse and reopening no longer show tooltips, as explicitly requested; their labels remain.
Existing motion, persistence and size limits are unchanged.

Verified: full frontend checks pass, including 435 tests. All six legend browser scenarios
pass, with added checks for the missing arrow icon, corner cursor, edge position and absence
of collapse/open tooltips after their former delay. A pointer placed exactly on the visible
upper-right border resizes both dimensions. Desktop 1440/1920 visual checks pass; axe finds
no legend violations and the browser reports no page errors. Evidence:
`/tmp/casechamp-ui-fix/border-{verify.log,e2e.log,visual.json,*.png}`.

The frontend image is deployed on port 8080. Production browser checks confirm resizing
from the actual border, no visible arrow button or collapse tooltip, and working collapse/reopen.
Frontend, backend and ClickHouse are healthy; only the frontend container was recreated.
