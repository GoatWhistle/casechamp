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
