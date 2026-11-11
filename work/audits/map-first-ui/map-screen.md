# Frontend audit: map screen (`/`), branch `feat/map-first-ui`

Scope: the map screen only. That covers the map overlays (toolbar, legend, zoom, hover card), the side
panel with its Чат / Сводка / Сценарий tabs, the panel resizer and region selection. Audits 1-5 from
`frontend-audit`, plus `impeccable` audit and critique passes, `review-animations` (SKILL.md and
STANDARDS.md read directly), `find-animation-opportunities` and `emil-design-eng`. The base commit is
`cdb2c2e` plus the uncommitted working tree from the git status on 2026-11-11. This is a read-only
pass: nothing under `frontend/src` was changed.

## How we checked

- **Stand.** Vite at `127.0.0.1:5187`, API at `:8001`, Chromium via Playwright. Chat is disabled on the
  backend (`CHAT_ENABLED=false`), so the error banner after sending is expected and not reported.
- **Matrix.** Widths 375x812, 720x450 at DPR 2 (200% zoom), 1024x768, 1440x900 and 1920x1080, plus
  `html { font-size: 125% }` at 375 and 1440. States: live, loading (4 s delay on `/api/v1/**`), full
  API error (503 on `/api/v1/**`), partial error (503 on region links), selected region
  (`?region=93000000`), panel at max and min width, and `prefers-reduced-motion: reduce`.
- **Commands.** `npm run rules`: 36 checks passed. `npm run typecheck`: clean. `npm run lint`:
  535 files, no fixes. Vitest was not run because it is known to fail in this environment. Neither
  `npm run build` nor `npm run e2e` was run: the stand had to stay up and must not be restarted.
- **Detector.** `impeccable detect --json` on `features/map-explorer`, `features/map-chat`,
  `road-scenario/{map-key,road-selection}.tsx`, `shared/ui/layout/panel-resizer` and `pages/map`
  found nothing (`[]`). Every finding below comes from the live pass and from reading the code.
- **axe.** `@axe-core/playwright` with wcag2a/aa, 21aa, 22aa and best-practice, at 1440 and 375, on
  the chat and summary tabs. The only violation is `target-size` (serious) on the OSM attribution
  link, which is 22.6 px tall.
- **Measurements.** `document.getAnimations()` was logged after each action. `elementFromPoint` rows
  measured the resizer hit area, and `getComputedStyle` measured the focus outlines. Scroll height
  and scroll-chain checks were done per tab. Probe output is in `shots/*.json`.
- **Method note.** This was a single-context `impeccable` critique. Assessments A and B were not split
  into sub-agents, and nothing was persisted to `.impeccable/critique/` because this audit was limited
  to writing a report and screenshots.
- **Scripts.** `frontend/screenshots/mfu-*.mjs`, which is gitignored. Screenshots are in
  `work/audits/map-first-ui/shots/`.

## Summary

The desktop composition works: the map comes first, the panel is resizable, keyboard and pointer
drag both work, and popovers, the select and the tooltip follow the motion tokens. Two layout defects
block the demo:

- At every width, the **Сводка** tab cannot scroll. Its list is cut at the fold. The mouse wheel does
  nothing, and keyboard focus scrolls the whole document so the map leaves the screen.
- **At or below 64rem** (1024, tablets, phones, 200% zoom) the chat gets about 38% of the viewport. At
  375 the message area is 67 px tall.

The motion layer replays a long stagger on every tab switch, keyboard switches included. Banners and
chat messages appear without any motion.

| Dimension | Score 0-4 | Main issue |
|---|---|---|
| Motion | 2 | Ranking and card stagger (320 ms) replays on each switch to Сводка, keyboard included; banner and messages have no enter or exit |
| UX and scenarios | 1 | Сводка cannot scroll; chat is crushed at or below 64rem; an API error blanks the whole screen |
| Visual system | 3 | One layer has two toggles; the proposed link and air links share one violet dash |
| Air, rhythm, scaling | 1 | At 375: metric select collapses to "Д", the legend covers the map, the separator strip intercepts taps; header collides at the 320 px panel |
| Anti-AI-slop and polish | 3 | Generic "данных атласа" chat copy, OSM ids in the road list, 2-decimal legend ticks |

`impeccable` audit health: a11y 2, performance 3, theming 3, responsive 1, implementation integrity
3. Total **12/20 (Acceptable)**. Nielsen heuristics, single-context estimate: **24/40**. The weakest are
visibility of system status, user control (Сводка is a dead end) and consistency.

**Findings: P0 2, P1 14, P2 13.**

## Findings

### P0: breaks the scenario or accessibility

#### 1. Сводка tab cannot scroll; keyboard focus scrolls the map away

- **Where:** `/` and `/?region=…`, tab Сводка, every width. The cause is in
  `features/map-explorer/map-panel.module.css:1-3`: `.panel` (an `aside`) has no block size, so its
  `ScrollArea` with `block-size: 100%` resolves to auto. `features/map-chat/map-chat.module.css:47-50`
  contributes: `.summary` is a flex item but is not itself a flex or grid container. MapPanel used
  to be a direct grid child of `.explorer`; it is now nested inside MapChat.
- **What is wrong:** with Tyva selected, the ScrollArea "Россия" measures 6026 px tall with
  `scrollHeight === clientHeight`, and the document is 6131 px tall at a 900 px viewport. The mouse
  wheel over the panel does nothing, because `overscroll-behavior: contain` on a ScrollArea with no
  scroll range swallows it (`window.scrollY` stays 0). The 59 settlement links below the fold
  cannot be reached. Tabbing into those links scrolls the whole document to `scrollY` 2088: the map,
  toolbar, panel header and tabs all leave the screen and the left half turns white. Without a
  selection, the ranking is also cut, at a document height of 994 px. Screenshots:
  `shots/1440-tyva-summary.png`, `shots/1440-tyva-summary-scrolled.png`,
  `shots/1440-tyva-summary-tabbed.png`, `shots/scroll-probe.json`.
- **Rule:** PRODUCT.md "No dead ends"; frontend-audit 2 (dead ends); AGENTS §10 "panels fill width".
- **Fix:** in `map-chat.module.css`, make `.summary` (and the scenario wrapper) a
  `display: grid; grid-template-rows: minmax(0, 1fr)` container. Also give `map-panel.module.css`
  `.panel` `block-size: 100%`. Add an e2e assertion that
  `document.documentElement.scrollHeight === innerHeight` on `/` for each tab, with and without
  `?region`.

#### 2. At or below 64rem (1024, 768, 375, 200% zoom) the panel is locked to 38% of the viewport and the chat is unusable

- **Where:** `features/map-explorer/map-explorer.module.css:11-13`.
  `.explorer[data-fullscreen="true"] { block-size: 100dvh }` has specificity 0,2,0, so it overrides
  the `.explorer { block-size: auto }` reset in the `max-width: 64rem` block (`:132-136`). With rows
  `62dvh auto`, the panel gets whatever is left over.
- **What is wrong:** at 375x812 the chat history ScrollArea is 67 px tall while its content is 482 px.
  The empty state is clipped through the ChatMark, and the suggestions and recent chats are invisible.
  Every answer would have to be read through a 67 px window. 1024x768 and 720 at DPR 2 (WCAG 1.4.10
  reflow at 200%) show the same squeeze. The Сценарий tab also scrolls inside about 200 px.
  Screenshots: `shots/375-home-chat.png`, `shots/375-tyva-chat.png`, `shots/1024-tyva.png`,
  `shots/720-zoom200.png`.
- **Rule:** AGENTS §10 "anything breaks at 375px"; frontend-audit 4 (375 and 200% zoom); WCAG 1.4.10.
- **Fix:** inside the `max-width: 64rem` block, reset `.explorer[data-fullscreen="true"]` to
  `block-size: auto` and give the panel `min-block-size: 100dvh`, so the page scrolls from the map to
  a full-height panel. The alternative is to put the panel into the existing `Sheet` primitive on
  narrow screens. Re-shoot 375, 1024 and 720@2x.

### P1: clearly visible

#### 3. On narrow screens the separator is an invisible, focusable strip that intercepts taps

- **Where:** `features/map-explorer/map-explorer.tsx:216-225` renders `PanelResizer` at every width.
  `map-explorer.module.css:15-18` gives it no reset at or below 64rem, and
  `shared/ui/layout/panel-resizer/panel-resizer.module.css:123-128` widens the hit area to 44 px.
- **What is wrong:** at 375 the separator spans the full 812 px height at x=33-77. It sits on top of
  the map (blocking panning there), most of the "Чат" tab (x=17-69) and the left edge of the composer.
  `elementFromPoint` returns `separator` at every y. It stays in the tab order with
  `aria-valuemin = aria-valuemax = 320`, so End and the arrow keys do nothing. Evidence:
  `shots/scroll-probe.json` (`hits`), `shots/375-separator-focus.png`.
- **Rule:** AGENTS §8 (keyboard, touch targets); WCAG 2.4.3; `impeccable audit` "broken touch
  interaction".
- **Fix:** do not render `PanelResizer` under `useMediaQuery("(max-width: 64rem)")`, or hide it with
  `display: none` in that media block. Either way, it leaves the tab order.

#### 4. At 375 nothing names the current metric

- **Where:** `map-explorer.module.css:95-107`. At or below 48rem the toolbar is `nowrap` and
  `.metric` shrinks to `min-inline-size: 0` against two fixed controls. `map-legend.module.css:101-103`
  hides the legend title at or below 64rem.
- **What is wrong:** the metric Select is 56 px wide and shows "Д" plus a chevron. With the legend title
  hidden, the colour scale has no name anywhere on screen. Screenshots: `shots/375-home-chat.png`,
  `shots/375-tap-region.png`.
- **Rule:** AGENTS §10 "anything breaks at 375px"; frontend-audit 4.
- **Fix:** at or below 48rem, wrap the toolbar into two rows: metric at full width, then network plus
  season. Keep the legend title visible.

#### 5. At 375 the overlays cover most of the map and the selected region lands under them

- **Where:** the overlay stack in `map-explorer.module.css:110-130` cannot be collapsed. The camera
  padding is hardcoded in `entities/region/osm-map/map-camera.ts:64` as
  `{ top: 96, right: 56, bottom: 144, left: 56 }`.
- **What is wrong:** the toolbar and legend cover y=16-300 of a 503 px map. After Tyva is selected or a
  region is tapped, the region sits under the legend and only Mongolia is visible. Screenshots:
  `shots/375-tyva-chat.png`, `shots/375-tap-region.png`.
- **Rule:** frontend-audit 4; DESIGN "data is the main visual".
- **Fix:** turn the legend into a `Disclosure`, collapsed by default at or below 64rem. Compute
  `fitBounds` padding from the measured rects of the toolbar and legend instead of constants.

#### 6. On touch, the hover card sticks after a tap, shows the wrong region and runs off screen

- **Where:** `entities/region/osm-map/map-hover.ts:36-54`. A tap fires `mousemove` but no
  `mouseleave`, and `moveend` re-picks a feature at the stale pointer after the camera flight.
  `features/map-explorer/hover-card.module.css:3-12` is fixed to the right of the pointer with no flip.
- **What is wrong:** after tapping Иркутская область, the card says "Республика Б…" (the region now
  under the old pointer) and is cut off by the right edge of the viewport. Screenshot:
  `shots/375-tap-region.png`; `hoverCardAfterTap: true` in `shots/mobile-probe.json`.
- **Rule:** AGENTS §5 "hover only inside `(hover: hover) and (pointer: fine)`"; review-animations #8.
- **Fix:** report hover only for `pointerType === "mouse"`, and render `HoverCard` only under
  `useMediaQuery("(hover: hover) and (pointer: fine)")`. Flip and clamp the card against the
  viewport and panel edges.

#### 7. Legend tick labels overlap

- **Where:** `features/map-explorer/map-legend.module.css:21-42`. The legend has a fixed width
  (`--legend-width` + 64 px), ticks are `white-space: nowrap`, and columns are `minmax(32px, 1fr)`.
- **What is wrong:** Население renders "40 тыс. 100 тыс400 тыс800 тыс1,7 млн3,4 млн", and Выручка
  компаний на жителя renders "50 тыс. 200 тыс450 тыс900 тыс1,4 млн4 млн". At 125% font, Hansen renders
  "4,00 10,0035,0060,0082,00120,00". Screenshots: `shots/legend-stack.png`,
  `shots/1440-metric-last.png`, `shots/1440-font125.png`.
- **Rule:** frontend-audit 4 (large system font); storytelling-with-data (legible scale).
- **Fix:** label only the bin boundaries that fit: first, middle and last, with the rest in
  `visually-hidden`. Alternatively stagger the labels onto two rows. Let the legend grow with the font
  size (`min-inline-size: max-content` on `.scale`, or a token width in `rem`).

#### 8. Panel header collides at the minimum panel width and at 125% font

- **Where:** `features/map-chat/map-chat.module.css:7-29`. `.title` is `white-space: nowrap` and
  `.heading` has no `min-inline-size: 0`.
- **What is wrong:** at the 320 px panel (Home key on the separator), "Вопрос к данным" runs into
  "Новый чат" and covers its plus icon. At 125% font the title and button touch. Screenshots:
  `shots/1440-panel-min.png`, `shots/1440-font125.png`.
- **Rule:** frontend-audit 4; AGENTS §10 "anything breaks".
- **Fix:** under `@container side-panel (max-width: 24rem)`, make "Новый чат" icon-only (it already
  has an `aria-label` and tooltip pattern), and truncate the title.

#### 9. Tabs control nothing: there is no tabpanel, no `aria-controls` and no content fade

- **Where:** `features/map-chat/map-chat.tsx:89-106` calls `Tabs` without children and toggles three
  sibling divs with `hidden`. `shared/ui/navigation/tabs/tabs.tsx:77` sets `aria-controls` only when
  children exist, and `:89-99` renders the tabpanel the same way.
- **What is wrong:** the page has zero `role="tabpanel"` elements, and every tab has
  `aria-controls=null`. Screen readers announce three tabs with no relationship to the content below.
  Because `panelRef` stays null, `useContentFade` never runs, so the content swap differs from the
  tabs on `/regions/:id` and `/sources`. Evidence: `shots/base-probe.json` (`tabpanels: 0`).
- **Rule:** WAI-ARIA tabs pattern; AGENTS §5 "content swap"; AGENTS §10 "element behaves differently
  from the same element on a neighbouring screen".
- **Fix:** extend `Tabs` with a `panels` slot (one node per tab, kept mounted, with role, ids and
  `hidden` set by Tabs), and use it in MapChat.

#### 10. The Сводка stagger replays on every tab switch, keyboard included, and runs past the budget

- **Where:** `features/map-explorer/ranking.module.css:18-21` (`--motion-rise-in` with a stagger) and
  `map-panel.module.css:14`. `--motion-rise-in` uses `--dur-slow` (320 ms) in
  `shared/styles/tokens/motion.css`. Going from `display: none` to visible restarts the keyframes
  each time.
- **What is wrong:** pressing ArrowRight from Чат to Сводка starts 8 or more `kf-rise-in` animations of
  320 ms with 0-280 ms delays, about 600 ms of motion on data that was already loaded. The selected
  region card rises again on every switch. Evidence: `tabKeyAnims` in
  `shots/interact-probe.json`, and rows caught mid-fade in `shots/1440-tab-keyboard-focus.png`.
- **Rule:** AGENTS §5 ("first load" stagger only, keyboard actions and cached data are not animated,
  UI under 300 ms); review-animations #2 and #4; STANDARDS frequency table.
- **Fix:** play the stagger once per data load, for example by latching an entered flag on first
  `animationend` or keying it on the query's `dataUpdatedAt`. Keep hidden panels painted-off without
  `display: none`, using `content-visibility: hidden` or `inert` with `visibility`. Bring
  `--motion-rise-in` under 300 ms, for example by moving it to `--dur-base`.

#### 11. Map canvas focus is invisible, and its accessible name is English

- **Where:** `entities/region/osm-map/osm-map.module.css:43-46` sets `outline: var(--focus-ring)`.
  `--focus-ring` is a colour only (`semantic.css:51`), so outline-style falls back to `none` and
  overrides the global ring. The MapLibre canvas keeps its default `aria-label="Map"`.
- **What is wrong:** Tab reaches the canvas (`:focus-visible` matches) with computed outline
  `none 3px rgb(0,122,252)`. No ring is drawn, yet the arrow keys pan the map. Evidence:
  `shots/1440-focus-step8.png`, `shots/1440-canvas-focus.png`, `shots/overlays-probe.json`.
- **Rule:** AGENTS §8 "`:focus-visible` is always visible"; WCAG 2.4.7; AGENTS §4 (Russian only).
- **Fix:** `outline: var(--focus-ring-width) solid var(--focus-ring)`. Pass MapLibre
  `locale: { "Map.Title": t("map:label") }`, or set the canvas `aria-label` after init.

#### 12. Zoom stack covers the OSM attribution, and the attribution is under the 24 px target size

- **Where:** `map-explorer.module.css:85-87` (`.zoom` at `inset-block-end: var(--space-16)`) and
  `osm-map.module.css:18-28` (attribution at `--space-4` from the bottom).
- **What is wrong:** the zoom box bottom is at y=879 and the attribution top at y=873.4, so the stack
  covers the top of "OpenStreetMap". axe flags `target-size` (22.6 px, serious) at 1440 and 375.
  Screenshots: `shots/crop-attrib.png`, `shots/states-probe.json`.
- **Rule:** WCAG 2.5.8; OSM attribution must stay legible.
- **Fix:** lift `.zoom` by the attribution height (a new token such as `--map-attribution-clearance`),
  and pad the attribution to 24 px tall.

#### 13. Touch targets below 44 px on the map screen

- **Where:** `features/map-explorer/map-zoom.tsx:38` (`size="compact"`, 36x36); the toolbar
  `Segmented` (57x36 and 59x36); `map-chat.tsx:85` ("Новый чат", 110x36); `CloseButton` and
  `HelpTip` in the selected card (36x36).
- **What is wrong:** the `touch-targets` check passes, but measured rects are 36 px tall on a screen
  meant for touch at 375. Evidence: the `small` arrays in `shots/base-probe.json`.
- **Rule:** AGENTS §8 "Touch targets at least 44px".
- **Fix:** under `(pointer: coarse)`, use the default size, or expand the hit area with the same
  `::before` technique the separator and attribution already use.

#### 14. An API failure blanks the whole screen, including the chat

- **Where:** `features/map-explorer/map-explorer.tsx:97` returns `ErrorState` instead of the explorer.
- **What is wrong:** with 503 on `/api/v1/**`, the screen shows a small "Сервер не ответил. Повторить"
  at the top of an empty white page at both 1440 and 375. The map frame, toolbar and panel disappear,
  including the chat, which does not depend on overview data. Screenshots: `shots/1440-api-error.png`,
  `shots/375-api-error.png`.
- **Rule:** PRODUCT "No dead ends"; frontend-audit 2 (error states); AGENTS §10.
- **Fix:** keep the layout and render the `ErrorState` centred inside `.stage` on `--map-water`, the
  way `MapLoading` does. Keep the panel, with the summary tab showing its own error.

#### 15. The scenario road list shows raw OSM ids and near-duplicate rows

- **Where:** `features/road-scenario/road-selection.tsx:42-53` and the `graph.json` keys `addRoad`,
  `removeRoad`, `change`, `addition` and `method`.
- **What is wrong:** rows read "Выбрать Алексеевское - Альметьевск (1345255575)" eight times in a row,
  differing only by way id; Tyva shows "Выбрать «Чуйский тракт» (129222251)" and similar. The HelpTip
  says "Единый снимок data-20261107", and other strings show "OSM {{id}}" and "от узла {{source}} к узлу
  {{target}}". Screenshots: `shots/1440-home-scenario.png`, `shots/1440-tyva-scenario.png`.
- **Rule:** the brief's copy rule (no technical ids shown to users); AGENTS §10 "generic phrases
  instead of specific ones".
- **Fix:** group segments by name or ref into one row per road, and disambiguate by road class and
  length or by endpoints, never by id. Describe the snapshot by date ("снимок от 7 ноября 2026").
  Keep ids out of visible text.

#### 16. Banners and new chat messages appear and disappear with no motion, and the composer jumps

- **Where:** `shared/ui/feedback/banner/banner.module.css` (no animation), `chat-message.module.css`
  (no animation) and `map-chat.tsx:169-180`.
- **What is wrong:** after sending, the user bubble, the status line and the danger banner pop in.
  The footer grows, so the composer jumps up and the history shrinks. Only button colour transitions
  are logged (`sendAnims` in `shots/interact-probe.json`). Screenshot: `shots/1440-chat-error.png`.
- **Rule:** AGENTS §5 "Everything is animated, including opening and closing of everything that pops
  up"; find-animation-opportunities "teleporting state".
- **Fix:** see opportunities 1-2 below. Give Banner a `--motion-fade-in` entrance with a
  `usePresence` exit on `--motion-fade-out`, and give appended messages `--motion-swap-in`.

### P2: polish

#### 17. The chat-only header sits over every tab, and landmarks are nested

- **Where:** `map-chat.tsx:77-88`; `map-panel.tsx:184` (an `aside` inside the MapChat `aside`).
- **What is wrong:** "Вопрос к данным" and "Новый чат" stay above Сводка and Сценарий, and "Новый чат"
  on the Scenario tab silently jumps to Чат. The panel title is a `<p>`, and the complementary landmark
  named "Вопрос к данным" contains a second complementary landmark. Screenshot:
  `shots/1440-tyva-scenario.png`.
- **Fix:** make the header neutral (a panel or region title) and show "Новый чат" only on the chat tab.
  Change the MapPanel root to `<div>` or `<section>`.

#### 18. One layer, three controls and labels

- **Where:** `features/map-explorer/road-legend.tsx:9` (Checkbox "Дорожный граф"),
  `road-selection.tsx:13` (Switch "Дорожный граф") and `map-key.tsx:4-9` ("Дорожный граф" swatch).
- **What is wrong:** the same toggle is a Checkbox on the map and a Switch in the panel, and the key
  that explains the red and blue lines exists only in the Scenario tab, while those lines are on the
  map in every tab. Screenshot: `shots/1440-tyva-scenario.png`.
- **Rule:** AGENTS §6 "one component per role"; AGENTS §10 "element behaves differently".
- **Fix:** keep the Checkbox in the map legend, move the `MapKey` swatches into `MapLegend`, and drop
  the Switch.

#### 19. The proposed link and air links are both violet dashes

- **Where:** `entities/region/osm-map/connection-layer.ts:27` (`--data-gain-3`, #5a4aa8, dashed);
  `use-transit-layer.ts:34-38` (`--mode-air`, #7a5af5, dash `[4,3]`); `map-key.module.css:53-56`.
- **What is wrong:** a proposed link drawn in a region with air routes is barely distinguishable from
  them. Screenshot: `shots/1440-tyva-chat.png` (air links), and the key in
  `shots/1440-tyva-scenario.png`.
- **Rule:** frontend-audit 3 ("colour meaning one thing").
- **Fix:** take the proposed link out of the violet family: use the gain hue with a casing and a solid
  wider stroke, and keep dashes for schematic air links only.

#### 20. Three different link counts in one card

- **Where:** `map-panel.tsx:91` ("Дополнительных связей 33"), `:113-125` (mode list, sum 64) and
  `RegionLinks` ("Маршрутов в выбранном сезоне: 59").
- **What is wrong:** the numbers do not reconcile and the labels do not state their scope.
  "Дополнительных" is unclear. Screenshot: `shots/1440-tyva-summary.png`.
- **Fix:** name the scope in every label (season, all seasons, with or without a calendar), or show one
  count with a breakdown.

#### 21. The resizer is undiscoverable and has no spoken value

- **Where:** `panel-resizer.module.css:130-145` (grip transparent at rest) and `panel-resizer.tsx:91-109`.
- **What is wrong:** the only cue is the cursor on hover. `aria-valuenow` is raw px (it reads "760"),
  there is no `aria-valuetext` or `aria-controls`, and reset works only on double-click.
- **Fix:** add a hairline grip at rest that thickens on hover, an `aria-valuetext` key such as
  "{{percent}} % ширины", Enter to reset, and `aria-controls` pointing at the panel.

#### 22. Illogical focus order across the overlays

- **Where:** DOM order in `map-explorer.tsx:139-198`. `OsmMap` renders the zoom slot inside the map
  frame, before the toolbar and legend.
- **What is wrong:** after the skip link, Tab goes canvas, attribution, zoom (bottom right), toolbar
  (top left), legend, and then the panel. The separator comes after the composer. Evidence:
  `tabOrder` in `shots/overlays-probe.json`.
- **Rule:** WCAG 2.4.3.
- **Fix:** order the overlay as toolbar, legend, then map and zoom. Put the separator between the map
  and the panel in the DOM.

#### 23. The tab focus ring cuts through labels

- **Where:** `shared/ui/navigation/tabs/tabs.module.css:46-48`. The outline is inset and the tabs have
  no inline padding.
- **What is wrong:** the ring is drawn over the first and last glyphs ("Сводка"). Screenshot:
  `shots/1440-tab-keyboard-focus.png`.
- **Fix:** add `padding-inline: var(--space-4)` and subtract it from the list `gap`.

#### 24. Header, tabs and content do not share a left edge

- **Where:** `map-chat.module.css:12` (header inline padding 24) versus `:31-33` (tabs 16).
- **What is wrong:** the ChatMark sits 8 px right of the tab icons, and the tab underline stops 16 px
  short of both panel edges. Screenshot: `shots/crop-header.png`.
- **Fix:** use one inline padding token for the header, tabs and panel content.

#### 25. Hover card and legend motion are off for their frequency

- **Where:** `hover-card.module.css:13`, `map-legend.module.css:12` and `map-legend.tsx:100-135`.
- **What is wrong:** the hover card fades in for 200 ms on every re-entry (a tens-per-day surface) and
  vanishes instantly. When a region is selected, the bottom-anchored legend grows by two rows with no
  bridge, so its top edge jumps.
- **Rule:** review-animations #2 and #9; AGENTS §5 (exit faster than enter; Tooltip skip rule).
- **Fix:** give the hover card `--dur-fast` in, `--dur-fast-exit` out via `useLatched`, and no
  animation when it re-shows within `--delay-tooltip-skip`. Swap the legend's transit rows through
  `Swap`.

#### 26. Chat copy is generic and the terms are mixed

- **Where:** `shared/i18n/locales/ru/chat.json:5,10,11,18,23` and `sessions.*`;
  `map.json` `connections.model`.
- **What is wrong:** one viewport says "данных" four times: "Вопрос к данным", "Спросите о данных
  атласа", "…по данным атласа.", "Спросите о данных…". The sessions copy mixes terms: "Удалить чат"
  opens "Удалить разговор?", next to "Мои чаты" and "История разговора". "Модельная авиа привязана…" is
  ungrammatical. `chat:sessions.list/local/search/noMatches` are orphaned since `chat-switcher` was
  deleted, so `tests/shared/i18n/used-keys.test.ts` will fail.
- **Fix:** run `humanizer`/`clarify`: give the intro a concrete hook (the selected region, or the
  three things the chat can do). Use one term, "чат". Write "Модельные авиасвязи привязаны…". Delete
  the orphaned keys.

#### 27. Legend precision and the network label flicker

- **Where:** `features/map-explorer/format-metric.ts:12` (`f.number(value, 2)` for Hansen thresholds)
  and `entities/region/network-mode-control/network-mode-control.tsx:21-26`.
- **What is wrong:** the ticks read "4,00 10,00 35,00 … 120,00", which is false precision. While
  overview loads, the network select says "Только дороги" and then renames itself to "Базовая сеть",
  so the toolbar width jumps. Screenshots: `shots/1440-home-chat.png`, `shots/1440-loading-1450ms.png`.
- **Fix:** use integer Hansen thresholds. Do not switch option labels on overview arrival: pick one
  wording, or skeleton the select until it is known.

#### 28. `--radius-chat` duplicates `--radius-lg`

- **Where:** `shared/styles/tokens/radius.css:6` (now 8 px, the same as `--radius-lg`), used in
  `chat-message.module.css:13` and `chat-composer.module.css:7`.
- **What is wrong:** an alias token with no distinct role. DESIGN §4 names four radius roles.
- **Fix:** delete the token and use `--radius-lg`.

#### 29. The stat help icon detaches from its label

- **Where:** `shared/ui/data-display/stat/stat.module.css:8-22`.
- **What is wrong:** when "Покрытие населения" wraps, the (?) lands at the far right of the cell, about
  60 px from the word. Screenshot: `shots/1440-tyva-summary.png`.
- **Fix:** give the label `inline-size: fit-content`, or render the help inline after the last word.

## Motion review (`review-animations`)

| Before | After | Why |
| --- | --- | --- |
| `ranking.module.css:19` `animation: var(--motion-rise-in)` replays on every tab show | Play once per data load; no animation on keyboard tab switch | Keyboard and cached data are never animated; STANDARDS frequency table |
| `--motion-rise-in` = `kf-rise-in var(--dur-slow)` (320 ms) | `--dur-base` (200 ms) | UI under 300 ms |
| `map-panel.module.css:14` card rise on every switch to Сводка | `Swap` keyed by region id, `--motion-swap-in` | Content swap goes through `Swap`; the card should move only when the region changes |
| Banner: no enter, no exit | `--motion-fade-in` + `usePresence` exit `--motion-fade-out` | Nothing pops in; exit faster than enter |
| Hover card: 200 ms fade on every re-entry, instant exit | `--dur-fast` in, `--dur-fast-exit` out, skip within `--delay-tooltip-skip` | Tens-per-day surface: reduce motion; tooltip skip rule |
| Tabs in MapChat: no content fade (no tabpanel) | `useContentFade` through a `panels` slot | Same element behaves the same on every screen |

What is right: Popover, Select and Tooltip use opacity with `translateY(±4px) scale(0.95)` at 160 ms on
`--ease-out` (`shots/overlays-probe.json`). The Select chevron rotates 200 ms. Keyboard resize and
double-click reset jump instantly. Under reduced motion every `--dur-*` drops to 1 ms and nothing moves
(`shots/rm-interact-probe.json`). The hover card moves by `transform`, without React re-renders.

**Verdict: block.** The stagger replays on a keyboard action and runs over the 300 ms budget. The banner,
messages and hover card have no exit.

## Animation opportunities (`find-animation-opportunities`)

| # | Location | Today | Purpose | Frequency | Suggested motion |
| --- | --- | --- | --- | --- | --- |
| 1 | `shared/ui/feedback/banner` | Chat error and storage banners pop in, and the composer jumps | Preventing a jarring change | Occasional | `animation: var(--motion-fade-in)` (opacity, `translateY(var(--shift-anchor))`, 200 ms, `--ease-out`); exit `--motion-fade-out` 140 ms via `usePresence` |
| 2 | `shared/ui/data-display/chat-message` | New user or assistant message appears instantly | Spatial consistency | Occasional | Once on append: `--motion-swap-in` (160 ms, opacity + 4 px rise); none for history restored from storage |
| 3 | `map-chat.tsx:89-106` | Tab content swaps with no bridge | Preventing a jarring change | Tens per day | The existing `useContentFade` (opacity 0.65 to 1, `--dur-fast`), skipped for keyboard (`modality.instant`) |
| 4 | `map-panel.tsx:79-86` | Selected card re-rises 320 ms on every show | State indication | Occasional | `Swap swapKey={id}` with `--motion-swap-in`/`--motion-swap-out` (160/110 ms) |
| 5 | `panel-resizer.tsx:105` | Double-click reset jumps 760 to 400 | Spatial consistency | Rare | `withViewTransition` around `reset` (`--dur-panel`, `--ease-drawer`), pointer only |

Rejected:

- Keyboard resize (arrows, Home and End): keyboard-initiated, so never animated.
- Legend colour changes on metric switch: colour change; AGENTS §5.
- Hover card row values: they change every pointer tick; `tabular-nums` only.
- Sliding tab underline: frequent, and `docs/design-decisions.md` (Tabs) already rejected it.
- Camera flights: already on `--dur-map` with reduced-motion handling.

## Before and after

No fixes were made; this was a read-only audit. Before screenshots are in `shots/`.

## Not checked

- Chat answers, streaming, tables and charts, because the chat backend is disabled locally.
- Scenario run, results and a proposed link on the map, which needs a backend calculation. Finding 19
  is based on tokens and paint code.
- Real touch devices and screen readers (NVDA or VoiceOver).
- `npm run build`, `npm run e2e` and Vitest.
- Map drag performance (frame timing) while the resizer is dragging. `ResizeObserver` calls
  `map.resize()` and `map.redraw()` each frame (`use-osm-map.ts`); no jank was visible headless.
