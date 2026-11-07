# Screens: Plexus

Date 2026-11-08. Data: read-only API (`work/api-contract.md`). Visual system: `work/design/design-system.html`.

## Shell
Header 64 px: wordmark (enter motion once per session), nav (Карта, Регионы, Сезоны, Методика, Источники) with icons, global search combobox (regions and settlements). Full width, no max-width. At 375 px: wordmark symbol, search icon button, menu sheet.

## Map (home, P0)
Task: see which regions depend on seasonal links and open one.
Layout: map fills the work area; left floating panel: metric (Связей в сезоне, Население, Компании), season segmented (Все, Лето, Зима), legend; right panel: overview stats or selected region summary with button «Открыть регион». Hover card follows the cursor. Selected region: three iso rings around its border. Index status banner: Hansen not connected yet, honest.
States: loading skeleton for panels and map frame, error with retry, region without geometry listed separately (Крым).

## Region
Task: understand how a region is connected and where data comes from.
Header: breadcrumbs, name, stats (н. п., население, связей по сезонам, компании). Body: region map with settlements (dots by population) and links drawn by mode and season style; side: links list grouped by mode with filters (mode chips, season segmented), each row opens a link sheet with source, date, confidence, frequency (assumed flagged). Below: settlements table (search, sort, pagination).
States: empty links («Ручных связей в выгрузке нет»), missing geometry.

## Seasons
Winter roads of Ugra: table with opening/closure dates, weight limit, timeline bars per season; filters by district.

## Method
Hansen formula, half-life, markets, component indices, what is and is not counted, status of computation.

## Sources
Catalog of sources with period, rows, link.

## 404
«Страница вне зоны доступа» with broken iso ring and link to the map.
