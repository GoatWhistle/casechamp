# Design audit: Plexus frontend

Date 2026-11-08. Branch `feat/frontend`. Method: Playwright (Chromium) against the dev server
(`127.0.0.1:5173` with the backend on `:8000`). All routes captured at 375/768/1440/1920, plus these
interactions: hover, ranking select, metric Select, season «Зима», search «тыв» and a no-result query,
wheel zoom, link sheet, mode chip. Errors simulated with 503 on `/api/v1/**`, loading with a 5 s delay.
Recaptured after the coordinator's fixes (mobile header, toolbar wrap, banner, method formula, backend
copy). Scripts: `frontend/screenshots/audit-*.mjs`, `dbg*.mjs`. Shots and the DOM probe (`probe.json`,
`interact.json`): `work/audits/shots/`. Not run: `npm run verify`, `npm run e2e`, 200% zoom pass.

Counts: **P0 1, P1 13, P2 14.**

## P0

1. **`/regions/93000000` at 375: horizontal overflow, 21 px.** At 375 the page is 396 px wide. The
   settlements card (`HEADER._header`, `DIV._field`, `_area _frame`) ends at right=396, so the
   "Найти населённый пункт" field and the "Дальше" pagination button are clipped (shot `375-region.png`).
   Rule: AGENTS §10, "anything breaks at 375px". Fix: `min-inline-size: 0` on the card's grid/flex child
   in `features/region-settlements/region-settlements.module.css`. Put the table inside the `DataTable`
   scroll area instead of letting it widen the card. Add an e2e assertion `scrollWidth === innerWidth`
   for every route at 375.

## P1

1. **Map legend missing at ≤64rem (768, 375).** The legend has `display:none` under `@media (max-width: 64rem)`
   (`features/map-explorer/map-legend.module.css:79`). On tablet and phone the choropleth has no key at all.
   Fix: render the legend as a compact bar under the toolbar, or as the first block of the panel.
2. **The legend has no values, and the scale hides differences.** The legend only says
   «Меньше … Больше». `stepScale` (`features/map-explorer/metric.ts:20`) cuts sextiles of the positive
   values, so Sakha (38 links) and Krasnoyarsk (115) get the same darkest colour (`1440-home.png`), and
   most of Siberia reads as "max". Zero (step 1) is barely distinguishable from the lowest class. Fix:
   pass the thresholds to `MapLegend` and print them under the swatches (`Intl`, e.g. 0, 1–3, 4–8 …).
   Make 0 a separate labelled swatch. Use rounded thresholds instead of raw quantiles.
3. **The season control looks active for metrics that ignore season.** With «Население», «Компаний»
   or «Выручка» selected, Все/Лето/Зима changes nothing on the map or in the ranking. Principle:
   no control without an effect (ui-ux-pro-max, feedback). Fix: in `map-toolbar.tsx`, disable it
   with a tooltip, or hide the segmented control when `metric !== "links"`.
4. **Region page: the mode chips filter the list but not the map.** With «Зимник» selected, the list shows
   one link, but the map still draws all 5 purple aviation lines (`i-1440-region-chip.png`). The selected
   chip is solid black, a colour that appears nowhere else. Selection is the blue accent or the white
   segmented pill (DESIGN.md: one accent for action and selection). Fix: pass the active modes to `RegionMap`
   (`entities/region/region-map`). Restyle the selected state in `shared/ui/forms/chip`.
5. **The region map has no key, and its marks are too heavy.** Settlements are pure-black dots, and Kyzyl
   is a black blob that hides the link origins. Line colours (purple aviation, teal river) are explained
   only by the list icons. There is no zoom, no hover and no dot-size key (`1440-region.png`). Fix: set
   the dots to `--text-secondary` at 60–70% opacity with a white halo, cap the radius, and add a
   mini-legend (modes plus dot size) in `region-map`. The selected link from the sheet should be
   emphasised on the map.
6. **The header wordmark rings read as a blurry glow.** The 62×44 brand link renders the 3-ring wordmark
   at about 22 px cap height, and the rings blur into a halo (`zoom-logo.png`). The DS says: below 48 px,
   use the x symbol with one ring, and use the full wordmark only from 96 px. Fix: in
   `shared/ui/brand/brand-mark`, use plain wordmark letters, or the small mark plus the word without
   rings, at header size.
7. **Error states drop the layout, and each page drops something different.** On `/`, the 503 state
   replaces the toolbar, map frame and panel with a 120 px block centred in an empty 900 px viewport.
   `/regions/93000000` loses its breadcrumb and title, and `/method` loses its page header, but
   `/regions` keeps its header (`e-1440-*.png`). AGENTS §10 says an element must behave like its
   neighbours. The copy «Повторите через минуту» also contradicts the instant «Повторить» button.
   Fix: render `PageHeader` and breadcrumbs always, and put `ErrorState` inside the failed panel (map frame,
   stats, list). Change the copy to «Сервер не ответил.» plus the button. Use the iso-ring empty
   illustration from the DS instead of the red triangle for full-panel errors.
8. **Skeletons don't match the layout.** The map skeleton is a 64 px grey band at the top of an empty
   frame, on both `/` and the region page, and it looks broken (`l-1440-region.png`, first
   `i-1440-hover.png`). The region stats skeleton is 2 full-width lines where the page shows 5 stat cells,
   so the layout shifts. List skeletons are generic text lines. Fix: the map skeleton should fill the frame
   (`block-size: 100%`), ideally with the brand pulse rings (the DS allows the pulse only while loading).
   Stats skeleton: 5 `Stat` placeholders. Table skeleton: rows at the real row height.
9. **`/regions` is one 4100 px table.** It has 82 rows with no search, no inline bars, no map and no
   sticky header (`1440-regions.png`). The same data on `/` has bars, so the two screens disagree.
   Principle: data is the main visual, so a dedicated data component should replace raw columns.
   Fix in `features/region-table`: add a bar cell for the sorted metric (reuse the `Ranking` bar), a
   search field, and a sticky `thead`. Optionally split into list + map detail at ≥90rem.
10. **`/seasons` has only a table.** The spec promised timeline bars per season, and the table doesn't
    show them. Route names use a spaced hyphen as separator («п.Белорусский - с.Ларьяк»). The «Сезон»
    column shows «2025» for winter 2024/25, which is ambiguous. At 375 the 7-column table scrolls, and
    the dates sit off-screen (`i-375-seasons-top.png`). Fix: in `pages/seasons`, add an open-to-close
    bar per route on a Dec–Apr axis grouped by season (labelled «Зима 2024/25»). Split the route
    endpoints and join them with an `arrow-right` Icon. At ≤48rem, switch to a card list.
11. **`/sources` copy and links.** Five names still use the middle dot («RFSD · финансы компаний»,
    «ФНС · доходы и расходы», «Освещённость · OpenGeoHub / VIIRS», «Югра · …», «МЧС · …»).
    One title is English: «Click That Hood / OpenStreetMap, regional geometry snapshot 2013». The
    «Открыть» column prints «нет данных» for rows with no link. At 375 the link column sits inside a
    458 px table in a 325 px scroller with no scroll affordance (`375-sources.png`). Fix: fix the backend
    reference copy (colon or a separate publisher field), leave the missing-link cell empty, and at
    ≤48rem move «Открыть» under the name as a ghost link.
12. **The method hero misreads.** The formula subscripts (i, j, ij) are in the accent blue and sit
    about 10 px below the baseline, so they read as links or footnotes. The decorative blob isoline at the
    right has roughly 1.1:1 contrast, looks like a smudge, and carries no time meaning. That breaks the DS
    isoline rule (rings only for travel-time zones or brand moments) (`1440-method.png`). Fix in
    `pages/method`: subscripts in `--text-primary`, `font-size: 0.6em`, `vertical-align: sub`. Remove the
    `Isolines` or replace it with a labelled 1/2/4 h example that explains the half-life.
13. **Touch targets below 44 px** (probe at 375): map zoom buttons 56×36, Segmented options 36 px tall,
    mode chips 36 px, «Открыть» links 93×36, header search 42 px, breadcrumb «Регионы» 57×22.
    Rule: AGENTS §8. Fix the min block size in the tokens/primitives (`Button sm`, `Segmented`, `Chip`,
    `TextField`), not per screen.

## P2

1. **The selection ring is heavy.** It has a 2 px black contour, a white knock-out band and 3 rings at
   about 4 px step, which looks like a sticker on dark fills (`1440-home-selected.png`). The DS says 3
   tones, 2 px lines, `--iso-step` 12 px, no black contour. The rings also appear static: on selection only
   the map transform (260 ms) and the panel animate, but the DS has the rings spread out. The region page
   has no ring selection at all. Fix: `russia-map.module.css` (drop the black stroke, use token step), plus
   the `kf-ring-in` stagger on `.selection`.
2. **Selection zoom is too tight.** The selected region fills about 80% of the frame, the context is lost,
   and Chukotka is cropped at the top. Fix: increase the fit padding in `use-map-view.ts` (e.g. 25%
   of the frame) and cap the zoom.
3. **Geometry seam:** a straight line crosses Chukotka at the antimeridian. It shows as a white line
   in the default view and as a black line when zoomed (`1440-home-selected.png`). Fix the geometry
   in the backend `geo/regions` or clip at 180°.
4. **The index banner pushes the ranking down.** It repeats in both the overview and the selected panel
   (and again on `/method`), so at 1440 only 7 of 8 ranking rows fit. After the first view, collapse it to
   a one-line `Banner` with a link.
5. **Label drift for one metric.** The same number is called «Ручных связей в сезоне» (toolbar, legend,
   ranking), «Ручных связей» (overview stat) and «Связей в сезоне» (selected panel, region stats), and
   «в сезоне» reads oddly next to the «Все» season. The season label is «Все» on `/` but «Все сезоны» on
   `/regions` and the region page. Pick one term per concept in `locales/ru/data.json`.
6. **Metric and season are local `useState`** (`map-explorer.tsx:32-33`). Only `?region=` persists, so
   reload or share drops «Компаний / Зима». Fix: move them to search params.
7. **Search popover is misaligned.** It is 490 px wide and anchored left of the 258 px input (x 938–1430),
   so it overruns the 32 px gutter. Settlements use a `users` icon (one concept, one icon: use a
   settlement/pin icon). The «тыв» query takes about 1.5 s with only a spinner. Fix: in
   `shared/ui/forms/combobox`, match the anchor width (min 360 px, right-aligned), and add a skeleton row.
8. **Link sheet details:** «Проверено 2025-03» is a raw ISO date (AGENTS §4: format with `Intl`). The title
   «г. Кызыл, село Кунгуртуг» joins the endpoints with a comma; use from/to with an `arrow-right` Icon.
   Mode «Авиация» appears twice (label and icon row).
9. **Ruble glyph in «76,2 млрд ₽»** is smaller and lower than the number. Set it in `Stat` as the
   same size with `--text-secondary`.
10. **768 header:** nav is icons-only although there is room for labels. Search moves to a second
    right-aligned row, so the header is 112 px tall and leaves an empty gap under the logo. Fix: at 48–64rem
    keep the labels and use a search icon button that opens the combobox.
11. **375 region stats:** 5 `Stat`s stacked one per row (about 330 px of height). Use a 2-column grid
    under 48rem as on `/`.
12. **A11y structure:** `/` has no `h1` (only `h2 Россия`). No map path is focusable (`0` focusable shapes),
    so map selection is mouse-only. Ranking and search are alternatives, but region focus and Enter should
    work too. Fix: visually hidden `h1` in `pages/home`, `tabindex`/`role="button"` per region path.
13. **Method page rhythm:** about 80 px empty bands above the status badge and below the reason line. The
    reason repeats the home banner word for word. Tighten `.formula` padding and cut the duplicated text.
14. **Three templated screens:** `/regions`, `/seasons` and `/sources` share the same template (title,
    lead, full-width bordered table), so the product looks generic past the map. P1 9–11 give each screen
    its own data component. Also add the brand isoline to empty and loading states, where the DS allows
    it and it is missing today.

## Brand isoline: where it stands

- Works: the map selection (it carries meaning, though it is too heavy, P2-1) and the 404 mark.
- Wrong or overused: the header wordmark at 22 px (P1-6), the method decorative blob (P1-12).
- Missing where the DS allows it: loading pulse in the map frame (P1-8), empty and error panels (P1-7),
  region-page selection (P2-1).

## Motion

Measured with `document.getAnimations()`. Popover 160 ms fade+scale, sheet 260 ms drawer, hover
card 200 ms fade, map pan/zoom 260 ms transform, ranking stagger 320 ms with 40 ms steps. Season colour
change is instant, which is correct. Gaps: the selection rings don't spread (P2-1), and the skeleton
pulse is not branded (P1-8). I found no motion that was excessive or off-token.
