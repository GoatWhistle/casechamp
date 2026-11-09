# Plexus: accessibility and edge-case audit

Date: 2026-11-08. Branch `feat/frontend`, after commit b60b45b plus the coordinator's fixes (mobile header,
banner stacking, method formula). This was a read-only live pass on http://127.0.0.1:5173 against the
real API on :8000. Scripts are in `frontend/screenshots/a11y-*.mjs` and screenshots in
`frontend/screenshots/a11y/`. Nothing under `frontend/src` was changed.

## What ran

- axe-core with tags `wcag2a, wcag2aa, wcag21a, wcag21aa, wcag22aa`. It covered 8 routes at 1440 and
  375 px, plus `/regions/93000000` with the link sheet open and the edge routes `/regions/35000000`,
  `/regions/14000000` and `/regions/xxx`. Result: **0 violations everywhere**. `color-contrast` came
  back incomplete on 2 nodes on `/regions/93000000`: the unit glyph and an overlapped map button.
- Keyboard walkthrough in Playwright (`a11y-kbd1..5.mjs`). It recorded focus element, size, ring and
  whether the element was off screen.
- Semantics dump (`a11y-sem.mjs`): headings, landmarks, live regions, SVG roles, table captions.
- break-ui through the real API: longest name `71800000`, zero links `14000000` (Белгородская),
  Crimea `35000000` (no geometry), `/regions/xxx`, `/?region=xxx`, empty search, empty settlement
  search, 503 on `/api/v1/**`, a 3 s delay on `/api/v1/**`, and widths 320/375/390.
- Touch targets and contrast: measured from DOM rects and computed colours (`a11y-targets.mjs`).

## Passed (verified live)

- The skip link is the first Tab stop (44 px high, visible ring) and moves focus to `#main`. The
  header nav has `aria-current="page"`; at 375 px it shows icon links of 44x44 with names.
- Every interactive element tested shows a 2 px `rgb(0,122,252)` ring (4.05:1 on white). Text inputs
  show it on the wrapper `.box`.
- Search combobox: typing «тыв» gives 4 options, ArrowDown sets `aria-activedescendant` with
  `aria-selected`, and Enter opens `/regions/93000000` with focus on the h1. «zzqq» gives
  `role=status` «Ничего не найдено». The first Esc closes the list and the second clears the input.
- Metric `Select`: Enter/ArrowDown open it, End and Enter pick an option, Esc closes, and focus stays
  on the trigger. Season `Segmented`: a real radio group in a `fieldset`/`legend`, arrow keys switch.
- Ranking: Enter on a row sets `?region=` and focus stays on the row.
- Link sheet: `role=dialog aria-modal`, named after the route. Focus moves to the title, Tab cycles
  Close, body, «Открыть источник», and Esc closes and returns focus to the original link.
- Sort buttons update `aria-sort`. «Дальше» pages the table and «Назад» is disabled on page 1.
- Changing route moves focus to the h1 on every page that has one.
- 503: all 7 data routes show `role=alert` «Сервер не ответил…» with «Повторить», and retry recovers
  each of them. 3 s delay: skeletons on the map, panel and region page, and nothing jumps when data
  arrives.
- Edge data: zero links shows an EmptyState, Crimea shows «Контура этого региона нет в подложке»,
  `/regions/xxx` shows «Регион не найден», `/?region=xxx` falls back to the Russia view, and a
  settlement search with no match shows «Ничего не найдено» with the pager hidden. Large numbers go
  through Intl: «2,1 трлн ₽», «1 540 486», «128,1 млн». The API's longest name is «Ханты-Мансийский
  автономный округ» (without «Югра»); it wraps cleanly in the h1 and the panel h2 at 320.
- Contrast: axe found no text failures. Placeholder 6.28:1, input border 3.58:1.

## Findings

No P0. 7 P1, 9 P2.

### P1

1. **Region page scrolls horizontally at phone widths.** Route `/regions/:id`, width ≤ 390.
   Steps: open `/regions/71800000` at 375 or 320. Observed: document `scrollWidth - innerWidth` is
   21 px for Тыва at 375, 64 px for ХМАО at 375 and 119 px at 320. The settlements card grows to the
   table's width (392 px), and the card header and search field go past the edge. Expected: only the
   table's `ScrollArea` scrolls. Cause: `.card` is `display:grid` with an implicit `auto` column, and
   the stale wrapper `div` has `min-width:auto`. Fix: in `shared/ui/layout/card/card.module.css`, give
   `.card` `grid-template-columns: minmax(0, 1fr)`. Alternatively, give the wrapper div in
   `features/region-settlements/region-settlements.tsx:86` its own class with `min-inline-size: 0`.
2. **Home has no h1, and routing to `/` loses focus.** Route `/`, all widths. The home page's only
   heading is h2 «Россия» or the region name. Steps: on `/nowhere`, press Enter on «Вернуться к
   карте» (the same happens with the logo or «Карта»). Observed: `document.activeElement` is BODY.
   Expected: one h1 and focus on it. Fix: add a visually hidden h1 in `pages/home/home-page.tsx`, or
   make the `MapPanel` title an h1. In the route-focus code, fall back to `#main` when a page has no h1.
3. **Touch targets under 44 px.** Measured at 375:
   - zoom buttons 56x36 ×3;
   - «Снять выделение» 36x36;
   - sheet «Закрыть» 36x36;
   - Segmented options 36 high;
   - mode chips 36 high;
   - pager «Назад»/«Дальше» 36 high;
   - «Открыть» on /sources 36 high;
   - breadcrumb «Регионы» 57x22;
   - `/regions` and settlements row buttons 20–41 high;
   - search input 42 high.

   This breaks frontend/AGENTS §8. Fix: give `Button size="compact"`, `Segmented`, `ChipGroup` and
   `CloseButton` `min-block-size: 44px` under `@media (pointer: coarse)`, or a ::before hit area.
   Make `.rowButton` in `features/region-table/*.module.css` fill the cell (`display:block`, block
   padding). Pad `.crumb`.
4. **Selecting a region on mobile gives no visible feedback.** Route `/`, 375. Steps: scroll the
   ranking and tap or press Enter on «ЯНАО». Observed: scrollY stays at 1027 and only the row
   highlight changes. The region header, stats and the map zoom are about 1000 px higher, off screen.
   Expected: the selected region is visible. Fix: in `features/map-explorer/map-panel.tsx`, on
   selection below 48rem, call `scrollIntoView` on the panel header and focus its h2
   (`tabIndex=-1`). Without motion when the selection came from the keyboard.
5. **The whole panel is a live region.** Route `/`. `aside[aria-live=polite]` holds about 400
   characters, so every region or season change reads out the whole panel. Fix: remove `aria-live`
   from the aside in `map-panel.tsx`. Add a visually hidden `role=status` with «Выбран регион: X»
   (new dictionary key).
6. **Icon buttons have no tooltip.** Affected: zoom ×3, «Вся Россия», «Снять выделение», sheet
   «Закрыть». No `role=tooltip` appears on hover or focus, and `aria-describedby` is null. This breaks
   frontend/AGENTS §6. Fix: wrap them in `Tooltip` in `map-explorer.tsx` and `CloseButton`.
7. **Settlements pager is silent, and focus goes off screen at 375.** Route `/regions/93000000`.
   «Показано 1–25 из 150» sits in no live region. At 375, after Enter on «Дальше», the focused button
   ends up off screen (`offscreen=true`) because the table height changes. Fix: in
   `region-settlements.tsx`, give `.pageText` `role="status"`. After a page change, scroll the table
   top into view instantly and keep focus on the button.

### P2

1. **The map is mouse-only.** The map `svg role=img` has 83 paths, none focusable, and the hover
   card only opens for a mouse. Keyboard users can still reach regions through the ranking, search
   and `/regions`. Fix: make the paths focusable (`role=button`, `aria-label`, Enter selects) in
   `entities/region` `RussiaMap`, or state in the map label that the list next to it is the
   alternative.
2. **Table rows use buttons to navigate.** `/regions` names are `<button class=rowButton>`, so a row
   cannot open in a new tab and a screen reader says "кнопка". After Back, focus goes to the h1 at
   scrollY 0 and the user loses their place. Fix: use `Link to=/regions/{id}` in `region-table.tsx`.
3. **Empty h1 while loading.** `/regions/:id` with a 3 s delay: h1 is "" until the data arrives, and
   route focus lands on an empty heading. No `aria-busy` anywhere. Fix: in `region-page.tsx`, render
   a skeleton h1 with visually hidden «Загрузка» and set `aria-busy` on the page section.
4. **Error replaces the whole page.** On `/`, `/regions/:id` and `/method` the error leaves no
   heading. `/regions`, `/seasons` and `/sources` keep their header. Fix: keep the page header and put
   `ErrorState` under it.
5. **Low-end choropleth steps are close to the sea colour.** The lightest steps on the sea
   `rgb(196,222,240)` measure about 1.2:1, and steps 1–3 differ from each other by under 1.5:1 (WCAG
   1.4.11 visual). The values are also in the legend and ranking, so this is P2. Fix: darken the
   first step in `tokens/palette.css` or add a darker region stroke.
6. **Repeated link text on /sources.** Eight links all read «Открыть». Fix: give each
   `aria-label` «Открыть источник: {name}» in `sources-page.tsx`.
7. **Kopecks on large money values.** The «Выручка компаний на жителя» ranking shows
   «5 596 491,00 ₽». Fix: `maximumFractionDigits: 0` in `features/map-explorer/format-metric.ts`.
8. **No hint for one-letter search.** Searching for one letter shows nothing. The API needs at least
   2 characters. Fix: show a hint status in `global-search.tsx`.
9. **Name sort follows the type prefix.** Sorting by «Название» orders by prefix («арбан…», «г.…»,
   «пгт…»), so page 1 is all арбаны. Fix: sort on the name without the type (backend
   `sort=name`), or label the column «Тип и название».

## Limitations

- Not checked: a real screen reader (NVDA/VoiceOver), 200% zoom, and the `/seasons` table with long
  district names.
- Contrast on map fills was computed, not perceptual.
- The first keyboard run on `/regions/93000000` once missed the links list; it did not reproduce in
  4 reruns and is treated as a flake.
