# Session state

Updated: 2026-11-08, Europe/Samara

## Explicit user instructions

2026-11-06:

> возьми шаблон https://github.com/GoatWhistle/template и поставь его сюда, только тот мд с табличкой что уже есть закинь в докс

<!-- plane-workspace-insights: explicit invocation only -->
Use Plane Workspace Insights, its six plane-* skills, and its Plane MCP tools only when the user explicitly invokes this plugin by name, selects it, invokes a $plane-* skill, or explicitly asks to use the Plane plugin. Mentions of tasks, projects, reports, dashboards, or Plane data alone do not activate this plugin. Once explicitly invoked, continue within that task's authorized scope. This rule applies in every working directory.
<!-- /plane-workspace-insights -->


2026-11-06:

> теперь задание хакатона добавим.

The rest of that user message is preserved verbatim in `brief/sources/2026-11-06-task.txt` and `brief/TASK.md`.

2026-11-06:

> https://github.com/GoatWhistle/casechamp привяжи гит

2026-11-06:

> забери в документацию ещё файл исаева.txt с рабочего стола. Это транскрибация спича с мероприятия открытия этого хакатона

2026-11-06:

> ещё инфа из презентации в A2_citations.md в загрузках

2026-11-06:

> у нас есть полная картина задачи теперь ?


2026-11-06:

> давай начнем с того что ты скачаешь все датасеты и сложишь их в отдельную директорию, создавай папку и туда складывай мд что это за датасет. Можешь использовать субагентов

> ты сначала датасеты из файла с табличкой скачай. КАрту рф пока забей. Мы посмотрим какие там вообще есть регионы и полноту данных. Затем подумаем как нам вообще в какой парадигме масштаба работать


2026-11-06:

> теперь проводи разведку по данным. ЧТо у нас есть и что мы можем построить и посчитать

2026-11-06:

> нам нужно что то вау. Что ещё можно сделать. Идеи

> надо ввп, возможности развития и тд. Критичность. Трафик привязать и тд

2026-11-06:

> закомить и запушь всё

2026-11-07:

> вникни в проект, создай ветку фронтенд от case-a2-transport-graph, короче попробуй понять что вообзще делаем и как и что

> смотри, мы делаем фронтенд как ты понял, изучи скиллы и прочее что есть, потому что активно будем их использовать

> нормальная архитектура и структура фронтедна в hack-template, мы должны использовать ее если кейсу это не мешает, только убрать от туда англ язык и тему, будем в одной теме и языке, русский язык светлая тема, с которой позжде определимся, сначала сделать надо базовую арху, чтобы позже мы щас с тобой определились с названием и крч темой вообще. пока базовая штука



2026-11-08:

> посмтри сессию клода в папке где фиксился зум и карта и доделай по его лпану все

> зум исправлен но все равно лагает . также архангельскую область куда то в пизду унесло на карта . и я не могу теперь эту карту двигать . исправь

> и все еще лагает очень

> Тормозит при любом действии

> твой план уже реализовали закомить изменения не включая в комит хтмл файлы в корне проекта и после комита пуша проверь можно ли еще лаги убрать их уже меньше стало но все равно при увелечении ументшении лаги есть

## Current state

- Updated 2026-11-08. Branch `feat/frontend`; commits and pushes only as andreysk0304, no trailers (user permission 2026-11-08).
- Product Plexus, mark "Градация" (`docs/brand/`, `frontend/src/shared/ui/brand/`). Design system `work/design/design-system.html`.
- Backend: read-only atlas API v1 over `DATA_DIR`, 104 unit tests. Hansen index export empty; UI says so.
- Frontend: all screens on real API, both audits (`work/audits/`) fixed except P2 antimeridian seam on Chukotka and keyboard focus of map regions (documented decision). `npm run verify` green, 347 tests.
- Home page: user picked «Сплетение» (others deleted); prototype `spletenie.html` in repo root, sources and data caveats in `work/design/home/`. Not ported to `frontend/src`; `/` still opens the map.
- README rewritten: assets from `cd frontend && npm run readme` (content in `docs/readme/readme.json`), hero shots `npm run readme:hero` with the app running. Old data README moved to `docs/data-pipeline.md`.

## Map repair, 2026-11-08

- Continued session `393d291b-93d0-462e-8a29-4e5109354f6c`. First repair and its limits: `work/map-performance/README.md`; follow-up for remaining lag, pan lock and Arkhangelsk: `work/map-performance/followup.md`.
- Repairs committed and pushed as eight commits `41c1037..377e1e8` on `feat/frontend` (identity Ivan Gerasimov from git config); root HTML files excluded.
- Zoom-lag follow-up (uncommitted on top of `377e1e8`): compositor-only gestures via `data-map-stage`, detail only at commit and only in viewport. Evidence: `work/map-performance/compositor.md`. Trackpad raster 6.0 s to 0.07 s at CPU x4; verify 353 tests and 13/13 e2e green; stand 8080 rebuilt.
- Fixed home-scale pan bounds. Focus uses largest polygon by area, not Arctic-island bounds or stale detail queries. Coordinates unchanged. Stale panel data now waits for matching ID.
- SVG CSS transforms batched to rAF; low detail during gestures, hidden off-screen shapes, Path2D hit testing, separate hover overlay, no selection waves; interruptible 260 ms flight. Canvas experiments were slower and removed.
- Native wheel/pinch, memoized panels, immediate top navigation, table document scroll and optional API `path_low` remain. API export docs: `docs/api.md`.
- Frontend verify: 347 tests, rules, TypeScript, lint and build passed. All 13 browser tests passed on preview and rebuilt stand 8080. 12 visual/axe cases at 375/1440 clean. Backend unchanged this follow-up; earlier Ruff/mypy and 104 unit tests passed; integration folder empty (exit 5). PostCSS warning remains.
- Corrected stress probe excludes tracing startup/teardown. CPU6/DPR2: hover p95 33.4→16.8 ms; wheel p95 unchanged 16.8 ms. Raster worker time increased; no general FPS or hardware-wide claim. Physical Safari/user device unverified.
- Frontend rebuilt and healthy on 8080; API 8001 unchanged. Final 13 browser tests passed (21.2 s).
- Original Chukotka antimeridian seam and missing index export remain outside this repair.

## How to continue

1. Commit/push the zoom-lag follow-up only if requested. Another session was editing `work/design/home/` concurrently (deleted prototypes, new `hero.js`); those changes are not ours.
2. Local containers use UI 8080/API 8001. Temporary Compose config for this repair: `/tmp/plexus-map-compose.yml`; root Compose file remains absent after the user's earlier deletion request.
3. Open product items outside this repair: antimeridian seam and index export from DuckDB.
