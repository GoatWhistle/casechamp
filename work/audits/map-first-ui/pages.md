# Frontend audit: non-map routes (map-first-ui)

Scope: audits 1-5 (motion, UX, visual system, scaling, anti-slop) over every route except `/`:
`/regions/93000000`, `/regions/71800000` (all three tabs), `/regions/00000000`, `/compare`,
`/compare?ids=93000000,24000000`, `/scenarios`, `/sources`, `/nope`, `/regions`, plus the global header
and search as seen on those pages. Branch `feat/map-first-ui`, HEAD `cdb2c2e` with the uncommitted
working tree from the git status at session start. Date 2026-11-11. Read-only: no source was changed.

## How we checked

- Stand: Vite dev `127.0.0.1:5187`, API `127.0.0.1:8001` with real data; Chromium via Playwright.
- Matrix: 1440x900 and 375x812 for every route state; header also at 768 and 1024; 200% zoom
  (720px at DPR 2) and `html{font-size:125%}` at 375/1440 for region, compare, sources, 404; touch
  emulation (`hasTouch`, coarse pointer) for targets and HelpTip.
- Axe (`@axe-core/playwright`, tags wcag2a/aa, wcag21a/aa, wcag22aa, best-practice) on every route at
  both widths: 1 violation total (`page-has-heading-one` on `/regions/00000000`, both widths).
- Measurements: CLS per route (PerformanceObserver), `document.getAnimations()` after each interaction,
  `document.startViewTransition` call counter, keyboard Tab walk, focus after route change and after
  chip removal, overflow culprits at 375, scenarios error latency (3.2 s, three 503 responses).
- Worst-case data (break-ui) injected at the API boundary with `page.route` (no source edits): 41-char
  region name, 13.3M population, 0.004 index, null index, all-zero and dominant-mode links, 65-char
  settlement, 180-char unbroken URL in a source note, null period, 1.2B rows.
- `npm run rules`: 36/36 checks pass. `impeccable detect` on the audited pages/features: 0 findings.
  Both guards miss everything below. `npm run verify` and `npm run e2e` not run (vitest is broken in
  this environment; e2e out of scope for a read-only pass).
- Impeccable critique ran degraded: single context (this audit is itself a delegated agent; the caller
  fixed the deliverable format), so Assessment A and B were not isolated.
- Scripts: `frontend/screenshots/pages-*.mjs`. Raw data: `shots/pages-report.json` (axe, targets,
  separators, Latin text, headings per route), `shots/pages-interact.log`, `shots/pages-vt.log`,
  `shots/pages-scenarios.log`. All paths below are relative to `work/audits/map-first-ui/`.

## Summary

The secondary screens are built from real primitives and hold up better than most hackathon UIs: axe is
clean, CLS stays under 0.03, focus moves to the `h1` on route change, the rank strip and isoline states
are product-specific. What lets them down is behaviour between screens: the same action (go to another
screen, remove a selection, say "not found", show an error) works differently depending on where it
happens, and three dead ends remain. At 375 the winter calendar, the sources list and the header search
results break.

| Dimension | Score 0-4 | Main issue |
| --- | --- | --- |
| Motion | 2 | View Transitions only on some links; compare stagger replays on every change and runs 320 ms |
| UX and scenarios | 2 | 404 links to a 404; region 404 offers Retry; scenarios error lies and has no exit |
| Visual system | 2 | Icon collisions (route, compare, snowflake), primitives overridden into lists, accent as series colour |
| Air, rhythm, scaling | 2 | Winter calendar 702 px wide at 375; sources and header search break at 375 |
| Anti-AI-slop and polish | 3 | Prose walls on the region page; technical ids and Latin in copy |

Impeccable audit health: accessibility 2, performance 3, theming 3, responsive 2, integrity 2:
12/20, "acceptable".

Findings: P0 1, P1 14, P2 15.

## Findings

### P0: breaks the scenario or accessibility

#### 1. Compare chips are toggles that silently remove a region, and focus is lost

- **Where:** `/compare?ids=…`, all widths; `features/region-compare/region-picker.tsx:48-50`.
- **What is wrong:** each selected region is a `Chip pressed` (`aria-pressed="true"`, name = region
  name). Pressing it removes the region. Nothing on screen or in the accessible name says it removes;
  a screen reader announces "Республика Тыва, toggle button, pressed". After removal focus falls to
  `body` (`pages-interact.log`: "focus after chip remove body") and all six cards replay their entrance.
  Evidence: `shots/compare-two-1440.png`, `shots/compare-four-1440.png`, `shots/pages-interact.log`.
- **Breaks:** frontend AGENTS §8 (focus return), §6 (one component per role), WCAG 4.1.2 and 2.4.3.
- **Fix:** add a removable token variant to `shared/ui/forms/chip` (label plus trailing `CloseButton`
  with `aria-label` "Убрать {{name}} из сравнения"); after removal focus the next chip or the combobox
  input; announce the change in a polite live region. Do not use `aria-pressed` for removal.

### P1: clearly visible

#### 2. Scenarios error state is wrong, slow and a dead end

- **Where:** `/scenarios` (matrix dataset absent); `features/scenario-lab/scenario-lab.tsx:15-22`,
  `shared/i18n/locales/ru/errors.json:12-16`, `shared/api/query-client.ts:7-10`.
- **What is wrong:** on page load, with no calculation started, the title says "Не удалось пересчитать
  индекс". The description says "Сервер не ответил." although the server answered 503
  `{"code":"data_unavailable"}`: there is no `errors:api.data_unavailable`, so the generic `kind.server`
  text is used. The only action is Retry, which cannot succeed. The skeleton shows for 3.2 s first
  because 5xx is retried twice. The page header above still promises "Добавьте связь между любыми
  точками". Evidence: `shots/scenarios-1440.png` (skeleton at 2.5 s), `shots/scenarios-error-1440.png`,
  `shots/scenarios-error-375.png`, `shots/pages-scenarios.log`.
- **Breaks:** root AGENTS "missing endpoints show an honest error state"; PRODUCT "No dead ends".
- **Fix:** add `errors:api.data_unavailable` ("Данные для расчёта сценариев на этом стенде не
  загружены."); give the catalog failure its own title (`scenario:errors.catalog`, "Расчёт сценариев
  недоступен"); add a secondary `ButtonLink` to the map scenario panel; in `shouldRetry` stop retrying
  an `ApiError` whose code is known and permanent.

#### 3. The 404 page sends users to another 404

- **Where:** `/nope`; `pages/not-found/not-found-page.tsx:21`.
- **What is wrong:** the secondary action "Список регионов" links to `/regions`, which has no route and
  renders the same "До этой страницы не добраться". Evidence: `shots/notfound-1440.png`,
  `shots/regions-index-1440.png`, `shots/notfound-regions-link-1440.png`, `shots/pages-vt.log`.
- **Breaks:** PRODUCT "No dead ends".
- **Fix:** link to `/compare` ("Сравнить регионы") or an action that focuses the header search; if a
  region index is wanted, add the route.

#### 4. Unknown region shows "Регион не найден" with Retry and no heading

- **Where:** `/regions/00000000`; `features/region-profile/region-profile.tsx:59-69`.
- **What is wrong:** a 404 renders a bare `ErrorState` with "Повторить" (retrying a 404), no `h1` (axe
  `page-has-heading-one`), tab title "Регион | Plexus", no way back but the header. The route 404 uses
  a different `StatusScreen` with art and two actions, so "not found" has two designs.
  Evidence: `shots/region-missing-1440.png`, `shots/region-missing-375.png`, `shots/pages-report.json`.
- **Breaks:** AGENTS §10 "an element behaves differently from the same element on a neighbouring
  screen"; axe best practice.
- **Fix:** on 404 render the same not-found screen as `NotFoundPage` (h1, actions "К карте" and
  "Сравнение"); keep Retry only for non-404 errors.

#### 5. Winter calendar doubles the page width at 375

- **Where:** `/regions/71800000?section=winter-calendar`, 375; `features/winter-calendar/winter-calendar.module.css:5-10,19-23,31`,
  `features/winter-calendar/calendar-row.module.css:7`.
- **What is wrong:** the document is 702 px wide (327 px horizontal scroll). The toolbar does not wrap,
  so the season Select and checkbox sit off-screen; the axis grid has hard minimums
  (180 + 160 + 240 px plus gaps), so month labels collapse into "ноябрьдекабрьянвар…"; the header
  border stops at 375. Evidence: `shots/region-ugra-winter-375.png`, `shots/crop-winter-calendar-375.png`.
- **Breaks:** AGENTS §10 "anything breaks at 375px width".
- **Fix:** `flex-wrap: wrap` on the toolbar and controls; below 48rem stack each row (name and dates on
  one line, track full width under it) and drop the axis to the track column; define the column
  template once (a custom property shared by axis and row) instead of two copies.

#### 6. Header search results are unreadable at 375

- **Where:** header search on every audited page, and the compare picker; `shared/ui/forms/option-list/option-list.module.css:55-65`.
- **What is wrong:** `.meta` is `white-space: nowrap` and `.label` is `min-inline-size: 0;
  overflow-wrap: anywhere`, so the region meta takes the row and settlement names shrink to about
  60 px, broken mid-word ("Мосто / вской", "Москов / ское"). Evidence: `shots/header-search-open-375.png`.
- **Breaks:** AGENTS §10 (375); break-ui "text overflows instead of wrapping".
- **Fix:** let the option wrap: label on the first line, meta on a second line (`flex-wrap: wrap;
  .meta { flex-basis: 100% }` or a two-row grid) below 30rem; meta truncates with ellipsis, never the
  name.

#### 7. Sources overflow at 375

- **Where:** `/sources`, 375; `features/source-catalog/source-catalog.module.css:15-25,36-39`,
  `shared/ui/layout/card/card.module.css:43-46`.
- **What is wrong:** 14 px page scroll with real data: the right-hand metadata block does not wrap and
  "Ссылки внутри набора" is clipped past the card edge. A long URL in a source note (worst case) adds
  44 px because Card description has no `overflow-wrap`. Evidence: `shots/crop-sources-375.png`,
  `shots/sources-375.png`, `shots/crop-sources-longurl-375.png`.
- **Breaks:** AGENTS §10 (375).
- **Fix:** wrap `.actions` under the text below 48rem; metadata `repeat(2, minmax(0, 1fr))`;
  `overflow-wrap: anywhere` on `Card` description; render URLs as links instead of raw text.

#### 8. Screen changes animate only from some links

- **Where:** all audited routes; `app/app-header/app-header.tsx:32,37-50`,
  `features/region-profile/region-profile.tsx:78`, `features/region-compare/metric-board.tsx:28`.
- **What is wrong:** `ButtonLink` and the global search navigate with a View Transition; the header
  nav, the brand, the "К карте" back link and the compare region links use bare `Link`/`NavLink` and
  swap instantly (`shots/pages-vt.log`: 1 call for "В сравнение", 0 for nav, back link, brand, bar
  label).
- **Breaks:** AGENTS §5 "screen change goes through the router's viewTransition"; §10 consistency.
- **Fix:** pass `viewTransition` on every in-app link (header, back link, metric board); better, add
  an `AppLink` primitive and a `rules` check that forbids bare `Link`/`NavLink` outside it.

#### 9. Header nav is icon-only up to 1024 px, with no tooltip, and active looks like hover

- **Where:** header at 375-1024; `app/app-header/app-header.module.css:74-78,55-58`,
  `app/app-header/app-header.tsx:37-50`.
- **What is wrong:** labels hide at `max-width: 64rem`, although at 1024 about 500 px of the row is empty. The
  icon-only links have no tooltip; the "Сценарии" route glyph and the "Источники" document glyph do not
  explain themselves. The active item and a hovered item get the same grey fill, so the current section
  is shown by a tint only. Evidence: `shots/header-hover-1024.png`, `shots/header-hover-768.png`,
  `shots/notfound-375.png`.
- **Breaks:** AGENTS §6 "an icon button has aria-label and a tooltip"; §8 state not by colour alone.
- **Fix:** keep labels down to 48rem; wrap icon-only links in `Tooltip`; mark the active item with a
  shape (2 px underline like `Tabs`) in addition to the fill.

#### 10. One icon means three things

- **Where:** header, region tabs, sources tabs; `features/region-profile/region-profile.tsx:38-46`,
  `app/app-header/app-header.tsx:16-21`, `features/source-catalog/source-topics.ts:4-9`.
- **What is wrong:** `route` is "Сценарии" in the header but "Связи" in the region tabs and sources
  topics; `compare` (bar chart) is "Сравнение" in the header and on "В сравнение" but "Сценарии" in the
  region tabs; `snowflake` is the winter season, the ice-crossing mode and the "Сезоны" topic.
  Evidence: `shots/crop-region-header-tabs-1440.png`, `shots/sources-1440.png`,
  `shots/crop-region-pairedbars-links-1440.png`.
- **Breaks:** AGENTS §6 "one concept, one icon, one canonical name".
- **Fix:** assign one icon per concept in `icons.ts` (links, scenarios, comparison, winter, ice crossing)
  and add an icon-concept map to the `consistency` check.

#### 11. "Сценарии" names two different features

- **Where:** header nav vs region tab; `features/region-profile/region-profile.tsx:41`,
  `pages/region/region-page.tsx:25-29`, `pages/scenarios/scenarios-page.tsx:11`.
- **What is wrong:** the nav item "Сценарии" opens the scenario lab whose h1 is "Новый маршрут и
  индекс"; the region tab "Сценарии" holds a single button "Рассчитать изменения на карте" that opens
  the road scenario on the map (panel tab "Сценарий"). Two features share one word; the tab is a link
  wearing a tab. Evidence: `shots/region-tyva-tab-scenarios-1440.png`, `shots/scenarios-error-1440.png`.
- **Breaks:** frontend-audit §2 "the same word for the same thing on every screen".
- **Fix:** give the lab one name used by nav, title and h1; remove the region "Сценарии" tab and put
  "Рассчитать изменения на карте" in the PageHeader actions next to "В сравнение".

#### 12. The region page's second card is a wall of prose

- **Where:** `/regions/*`, "Доступность при планировании поездки";
  `entities/accessibility/comparison/comparison-tables.tsx:95,102,103,110`,
  `entities/accessibility/comparison/accessibility-comparison.tsx:35,45-57`,
  `shared/i18n/locales/ru/accessibility.json:3,24,32`.
- **What is wrong:** three tables wrapped in four paragraphs, a banner and two provenance lines (about
  140 words at 1440, a full screen at 375). Text appears in three styles: 14 px secondary, unstyled
  16 px primary `<p>` (table titles and footnotes), 12 px caption. Table titles are plain paragraphs,
  not captions. Evidence: `shots/crop-region-accessibility-1440.png`, `shots/region-tyva-375.png`.
- **Breaks:** AGENTS §10 "a paragraph of explanation where a signature data component would do";
  DESIGN §3 one style per level.
- **Fix:** lead with one data component (per-season before/after delta, half-life Segmented on top),
  move method text into a `Disclosure` "Как считали" or HelpTips, use `DataTable` captions in one
  token style, drop provenance from the card (see 13).

#### 13. Technical identifiers and raw formats reach the UI

- **Where:** region and sources pages; `features/region-profile/index-card.tsx:51-55`,
  `entities/accessibility/comparison/accessibility-comparison.tsx:45-50`,
  `features/winter-calendar/calendar-row.tsx:64-67`, `shared/i18n/locales/ru/profile.json:9`,
  `features/source-catalog/source-catalog.tsx:67`.
- **What is wrong:** "Модель: hansen-release-20261107", "Модель hansen-planned-v1, исходный снимок
  data-20261107.", calendar facts show `source_file`, copy mentions "CSV" and "README", source notes
  carry raw URLs, and periods arrive as free strings, including ISO "2026-11-07" and a 60-character
  sentence. Evidence: `shots/crop-region-accessibility-1440.png`, `shots/region-tyva-1440.png`,
  `shots/crop-sources-period-1440.png`, `shots/pages-report.json` (`latin`).
- **Breaks:** AGENTS §4 dates via `Intl` ru-RU; task copy rules (no technical ids).
- **Fix:** show "Расчёт от 7 ноября 2026" formatted from the artifact date, keep versions on `/sources`;
  ask the backend for structured `period_start/period_end` and format them; turn URLs into links.

#### 14. Source topics and "where used" are hard-coded and already wrong

- **Where:** `/sources`; `features/source-catalog/source-topics.ts:10-32`.
- **What is wrong:** ids missing from `GROUPS` fall back to "network", so "Ставропольский край: реестр
  ОМС" (a medical insurance registry) is listed under "Связи и перевозки"; unknown ids get the usage
  text "Его записи не подключены к экранам приложения", including `network-model`, whose model pairs
  the region accessibility card describes. Evidence: `shots/crop-sources-period-1440.png`,
  `shots/sources-1440.png`; API ids in `GET /api/v1/sources`.
- **Breaks:** AGENTS §2 no hard-coded domain arrays; §3 the backend owns logic.
- **Fix:** the backend returns `topic` and `usage` per source; unknown values render in a neutral
  group and never claim "not used".

#### 15. The global nav disappears on the home screen

- **Where:** every audited route vs `/`; `app/root-layout/root-layout.tsx:10,17`.
- **What is wrong:** the header with nav and search exists on all five audited routes but not on `/`.
  From the home map there is no link to `/sources` or `/scenarios`; following "К карте" from a region
  drops the nav. Evidence: `shots/root-after-back-1440.png` vs `shots/region-tyva-1440.png`.
  Coordinate with the map audit.
- **Breaks:** AGENTS §10 consistency between neighbouring screens.
- **Fix:** one header on every route (a compact variant over the map), or the same nav inside the map
  panel.

### P2: polish

#### 16. Compare stagger replays on every change and runs 320 ms

- **Where:** `/compare`; `shared/ui/layout/card/card.module.css:13-16`,
  `shared/styles/tokens/motion.css:61`, `features/region-compare/metric-board.tsx:48`.
- **What is wrong:** `--motion-rise-in` uses `--dur-slow` (320 ms); removing or adding a region re-runs
  the stagger on all six cards (`pages-interact.log`, "anims after chip remove").
- **Breaks:** AGENTS §5 "UI animations are shorter than 300ms", stagger is for first load only.
- **Fix:** `--dur-base` for rise-in; latch the entrance on first mount (`useLatched`) so data changes
  only update bars.

#### 17. Tabs jump, Segmented slides; colour changes animate

- **Where:** region and sources tabs, header links; `shared/ui/navigation/tabs/tabs.module.css:19-34`,
  `shared/ui/forms/segmented/segmented.tsx:59`, `shared/styles/tokens/motion.css:45-50`.
- **What is wrong:** the Tabs underline crossfades `border-bottom-color` (160 ms) between tabs while
  Segmented uses `useSlidingIndicator`; `--transition-control(-press)` animates `background-color`,
  `color`, `border-color` on every control (`pages-interact.log`).
- **Breaks:** AGENTS §5 "colour changes are not animated", §10 consistency.
- **Fix:** Tabs indicator through `useSlidingIndicator` (transform only); remove colour properties
  from the control transition tokens, keep `scale`.

#### 18. "К карте" is a 1376 px wide, 22 px tall link

- **Where:** `/regions/*`; `features/region-profile/region-profile.module.css:5-11`,
  `features/region-profile/region-profile.tsx:78-81`.
- **What is wrong:** the grid stretches the inline-flex link across the row: a click on empty space at
  x=900 navigates to the map (`pages-interact.log`); height is 22 px under touch emulation.
- **Breaks:** AGENTS §8 44 px targets.
- **Fix:** `justify-self: start; min-block-size: var(--target-min)`, or a ghost `ButtonLink`.

#### 19. Region page layout leaves the right column empty and buries settlements

- **Where:** `/regions/*` at 1440; `pages/region/region-page.tsx:31-53`,
  `features/region-profile/region-profile.module.css:12-18,34-37`, `features/region-profile/seasonal-links.tsx:18-22`.
- **What is wrong:** the aside ends at y≈740 and the right column stays empty for 2000-4500 px; the
  settlements `Disclosure` hangs under the grid; when open, its five KPI stats sit unboxed and touch
  the table card, and "Населённые пункты" appears three times; for Ugra, "Только в один сезон" lists
  40+ rows, pushing settlements to y≈5300. Evidence: `shots/region-tyva-1440.png`,
  `shots/crop-region-settlements-1440.png`, `shots/region-ugra-1440.png`.
- **Breaks:** AGENTS §7 "width is filled with panels"; DESIGN "no KPI tiles without a conclusion".
- **Fix:** sticky aside; settlements as a tab or a Card in the main column with the stats inside it;
  cap the seasonal list at about 8 rows with "Показать все".

#### 20. PairedBars hide small values, render empty charts and rely on colour

- **Where:** region "Лето и зима"; `shared/ui/data-display/paired-bars/paired-bars.tsx:23,39-54`.
- **What is wrong:** with one dominant mode (12 845 vs 5) every other bar disappears; all-zero data
  renders six empty rows of "0 0"; values are read as "26 26" with no season, and season is told apart
  by colour and order only. Evidence: `shots/crop-pairedbars-dominant-375.png`,
  `shots/crop-pairedbars-allzero-1440.png`, `shots/crop-region-pairedbars-links-1440.png`.
- **Breaks:** break-ui (fragile scale, empty case); AGENTS §8 not by colour alone.
- **Fix:** minimum visible width for non-zero bars; `EmptyState` when every value is 0; visually
  hidden season label inside each value.

#### 21. Winter calendar fakes its headings

- **Where:** `features/winter-calendar/winter-calendar.tsx:30,87-89`,
  `features/winter-calendar/winter-calendar.module.css:11-13,45-51`.
- **What is wrong:** the section title is a `<strong>` styled larger than the district `h2`s, so the
  outline is inverted; districts are `Card`s with `{null}` children and overridden radius and padding.
  Evidence: `shots/region-ugra-winter-1440.png`, `shots/pages-report.json` (`heads`).
- **Breaks:** DESIGN §3 "screens write no h2-h6 by hand"; AGENTS §3 no home-made analogues.
- **Fix:** wrap the calendar in `Card` (title, actions = Select and Checkbox); districts as row-group
  headers of the schedule.

#### 22. Sources list is a Card stripped into rows, with drifting columns

- **Where:** `/sources`; `features/source-catalog/source-catalog.module.css:1-39`,
  `features/source-catalog/source-catalog.tsx:54-96`.
- **What is wrong:** `.catalog .entry` removes Card border, radius and shadow to fake a list;
  "Период/Записей" start at x=1043 or x=1059 depending on whether the trailing slot is a 48 px icon or
  64 px text; "Ссылки внутри набора" wraps into three lines; rows are 170 px tall for two lines of text.
  Evidence: `shots/crop-sources-period-1440.png`, `shots/sources-1440.png`.
- **Breaks:** AGENTS §3 (repeated block becomes a component), §7.
- **Fix:** a list/table primitive with fixed columns (title and note, period, rows, link); fixed-width
  trailing slot; "внутри набора" as a `StatusBadge`.

#### 23. Compare controls misalign and the limit hides in a placeholder

- **Where:** `/compare`; `features/region-compare/region-compare.tsx:23-28`,
  `features/region-compare/region-picker.tsx:38,48-50`.
- **What is wrong:** the season Segmented has no visible label, the "Режим транспорта" Select has one,
  so they sit 14 px apart vertically; at four regions the limit message becomes the placeholder and is
  cut to "Сравниваются до четырёх"; a long chip ("Ханты-Мансийский автономный округ — Югра") overflows
  375 by 18 px. Evidence: `shots/compare-two-1440.png`, `shots/break-compare-1440.png`,
  `shots/crop-compare-longchip-375.png`.
- **Fix:** label both or neither and align to the field row; show the limit as helper text and disable
  the input; chips `max-inline-size: 100%` with truncation and a tooltip.

#### 24. Compare series borrow the action and loss colours

- **Where:** `/compare`; `shared/styles/tokens/semantic.css:89-90` (`--series-1: blue-600`,
  `--series-2: orange-3`), used by `features/region-compare/region-picker.module.css:27-34` and BarChart.
- **What is wrong:** region 1 is drawn in the action blue (buttons, focus, selected chips); region 2 in
  a rust that reads as loss. Evidence: `shots/compare-two-1440.png`.
- **Breaks:** DESIGN §2 "the accent means one thing; it never decorates".
- **Fix:** a categorical palette outside the action and status hues, checked with the dataviz validator.

#### 25. Header at 375: search off the gutter, two search fields on compare

- **Where:** `app/app-header/app-header.module.css:60-65,80-93`; `/compare`.
- **What is wrong:** the wrapped search starts at x=92 instead of the 24 px gutter; on `/compare` two
  near-identical fields stack ("Регион или село", "Название региона"). Evidence: `shots/notfound-375.png`,
  `shots/compare-two-375.png`.
- **Fix:** full-width search below 48rem; picker placeholder "Добавить регион в сравнение".

#### 26. Region tables scroll sideways at 375 without a cue

- **Where:** `/regions/*`, 375; `entities/accessibility/comparison/comparison-tables.tsx`.
- **What is wrong:** columns are cut mid-word ("Потенци…", "0 из 28 05…") inside the card; nothing shows
  that the table scrolls. Evidence: `shots/region-tyva-375.png`.
- **Fix:** stacked rows below 30rem (season as row header, metrics as a definition list), or a sticky
  first column plus an edge fade.

#### 27. Copy: Latin, genitive fragments, data separators

- **Where:** region, compare, calendar, sources; `features/region-compare/compare-metrics.ts:45-66`,
  `features/winter-calendar/calendar-row.tsx:81`.
- **What is wrong:** "Доступность рынков Hansen" (Latin) on region and compare; compare card titles are
  genitive fragments ("Дополнительных связей", "Населённых пунктов", "Компаний"); route names render
  " - " separators ("п.Белорусский - с.Ларьяк"), a source note shows an em dash ("ограничения — в
  README"). Evidence: `shots/compare-two-1440.png`, `shots/region-ugra-winter-1440.png`,
  `shots/sources-1440.png`, `shots/pages-report.json` (`seps`, `latin`).
- **Breaks:** AGENTS §4 (no em dash or dash separators, Russian only).
- **Fix:** "Индекс доступности рынков (Хансен)"; nominative titles; split route endpoints with the
  arrow `Icon` as `LinkList` does; ask the backend to drop the dash from notes.

#### 28. Empty and error states float in a void, in two visual languages

- **Where:** `/compare` empty, `/scenarios` error, `/regions/00000000`;
  `shared/ui/states/error-state/error-state.tsx:26`, `shared/ui/states/empty-state/empty-state.tsx:18-21`.
- **What is wrong:** small centred blocks in a 1440x700 blank canvas; ErrorState has a 20 px icon,
  EmptyState a 64 px ringed art. The compare empty state offers no shortcut. Evidence:
  `shots/compare-empty-1440.png`, `shots/scenarios-error-1440.png`, `shots/region-missing-1440.png`.
- **Breaks:** AGENTS §7 (no narrow centred column), DESIGN §5 states.
- **Fix:** one art slot for both states (danger-toned rings for errors); compare empty shows suggested
  regions as chips (highest and lowest index) inside the board area.

#### 29. Icon links: identical names, no tooltips

- **Where:** "Только в один сезон" and sources; `entities/link/link-list/link-list.tsx:30-31`,
  `features/source-catalog/source-catalog.tsx:75-84`.
- **What is wrong:** 40 links named "Открыть источник" on the Ugra page; icon-only, no tooltip.
  Evidence: `shots/region-ugra-1440.png`, `shots/pages-interact.log` (Tab stops 18-21).
- **Breaks:** AGENTS §6 tooltip on icon buttons; WCAG 2.4.4.
- **Fix:** name "Источник: из {{from}} в {{to}}" and wrap in `Tooltip`.

#### 30. Missing motion on the calendar comparison

- **Where:** `features/winter-calendar/calendar-row.tsx:94-95`.
- **What is wrong:** "Сравнить с 2024/2025" makes previous-year bars and facts appear instantly (code
  read: conditional render, no transition on `.bar`).
- **Breaks:** AGENTS §5 "everything that pops up animates".
- **Fix:** the previous bar enters with `clip-path: inset(0 100% 0 0)` to `inset(0)` over `--dur-base`,
  `--ease-out`, via `@starting-style`; reduced motion gets the fade.

## Motion review (review-animations, find-animation-opportunities)

| Before | After | Why |
| --- | --- | --- |
| Header `NavLink`, back `Link`, metric-board `Link` without `viewTransition` | `viewTransition` everywhere through one link primitive | Screen change must look the same from every link (finding 8) |
| `--motion-rise-in` at `--dur-slow` 320 ms, replayed on data change | `--dur-base`, latched to first mount | UI under 300 ms; stagger is a first-load cue (16) |
| Tabs underline crossfades `border-bottom-color` | Sliding indicator with transform | Same group-selection behaviour as Segmented (17) |
| `--transition-control(-press)` animates colour | Animate `scale` only | AGENTS §5 bans colour animation (17) |

Rejected opportunities: animating compare bar widths on season switch (functional data being read);
header nav hover motion (tens per day); skeleton-to-content crossfade on the region page (CLS is
already 0.02 and the swap is a single frame). Verdict: block on findings 8 and 16, the rest is close.

## What held up

- Axe: 20 of 22 route captures with zero violations (the two misses are `/regions/00000000` at both
  widths); CLS 0.0002-0.027 on every route.
- Skip link first in Tab order, 2 px focus rings on every stop, route change focuses the `h1`, Tabs
  have roving tabindex and arrow keys, combobox closes with a 140 ms scale-out.
- HelpTip opens on hover, keyboard focus and touch tap (Chromium); compact controls grow to 44 px on
  coarse pointers.
- 200% zoom: no overflow on region, compare, sources, 404. Font 125%: only sources at 375 overflows.
- Long settlement names in `LinkList`, null index (Banner) and empty seasonal list (EmptyState) render
  correctly; numbers are `Intl`-formatted with tabular figures.
- Reduced motion turns the compare stagger into a fade and collapses durations.
- Distinctive pieces worth keeping: the index rank strip, isoline empty states, the 404 art.

## Not checked

Real iOS Safari (tap-to-focus for HelpTip), screen readers, 768/1920 full matrix (header only at
768/1024), slow-network loading states other than `/scenarios`, `npm run verify` and `npm run e2e`.
