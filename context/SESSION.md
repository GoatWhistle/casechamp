# Session state

Updated: 2026-11-07, Europe/Moscow

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



## Current state

- Branch `feat/frontend` created locally from `origin/case-a2-transport-graph` (no common history with `main`). Nothing committed; user owns git.
- Case A2 data work lives in `etl/`, `data_manual/`, `docs/indices.md`: Hansen market access for 155k settlements, scenarios road/summer/winter. `frontend/atlas/` is the teammates' Next/shadcn prototype on static JSON; kept as reference, excluded from Biome.
- Copied into the working tree: `skills/`, `.claude/`, `.agents/`, root and frontend agent files and the template `frontend/` from `main`; `brief/` and `context/` from `chore/project-research`. `core.symlinks=true` set locally so skill links are real symlinks.
- Template frontend reduced to RU only and one light theme: EN dictionaries, locale and theme switches, `shared/theme`, dark tokens and the boot script removed; check `theme-parity` replaced by `single-theme`. Rules docs updated. Placeholder mark extracted to `docs/brand/symbol.svg`.
- Earlier research (economic connectivity, EDA, traffic) is on `chore/project-research` under `work/research/`, `work/eda/`.

## How to continue

Name chosen by the user 2026-11-08: Plexus (English names only). Logo direction: concept 9 "Изохроны" (rings around the wordmark) from `work/brand/plexus.html`; refinement page `work/brand/isochron.html` (build: `ONEST_DIR=<fontsource onest files> python work/brand/build_iso.py`). Waiting for the user to pick a variation and parameters. Then, per user: port the mark into the design system (`work/design/`, `frontend/` tokens, `docs/brand/`), the interface (header, tab, loader), social cards and icons via `site-identity`. Visual style: Mapbox light, small radii (2–8 px), RU only, one light theme.

## Pitfalls already hit

- `git restore --source=main -- frontend` deletes `frontend/atlas`; it was restored from HEAD. Restore single paths only.
- `presentation/` is absent, so brand scripts read the mark from `docs/brand/symbol.svg`.
- `public/indices.json` of the atlas is empty: regional DuckDB results are not in git.

## Red checks

None. 2026-11-07: `cd frontend && npm run verify` green (36 rules, 280 tests, build); `npm run e2e` 1 passed; shots 375/1440 live and error viewed.
