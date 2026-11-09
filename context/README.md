# Project context

Project: «Атлас связности», кейс А2 — транспортная связанность территорий.
Updated: 2026-11-08, Europe/Moscow. Проверено по текущим файлам и Git; новые расчёты не запускались.
Direction: «Транспорт и территории». Event name not supplied.
Deadline from supplied text: 10 November, 23:59; year and timezone unknown.
Defense: 13 November; year and start time unknown.
P0 scenario: предложен пилот Югры с изменением сезонной связи. Конкретный объект и сценарий пользователем пока не выбраны; эффект решения не рассчитан.

## Current facts

| Topic | Status | Current fact | Evidence |
|---|---|---|---|
| Git | pushed | Локальная `feat/transport-graph`; HEAD и `origin/case-a2-transport-graph` — `20beaba58b0b4458983ea267a79b92d0941662e5`. Интеграция, атлас, тесты и документация отправлены в GitHub; `context/` остался локальным | `git log`, `git rev-parse`, `git status` |
| Атлас | implemented | 82 региона, 155 412 НП в исходной выборке, 997 записей дополнительных связей. Карта и карточки маршрутов, сезон/вид транспорта, источники, сравнение покрытия регионов | [frontend](../frontend/atlas/README.md) |
| 8 новых групп | integrated | RFSD, ФНС revexp, освещённость, зимники Югры, события МЧС, расписания, обследования потока, северный завоз. Локальная `data/additional.duckdb`: 26 таблиц; агрегаты экспортированы в атлас | [ETL](../etl/additional_data.py), [каталог](../datasets/additional/README.md) |
| Экономика | implemented | Региональные и отраслевые срезы компаний/выручки; ФНС отдельно; 1 808 061 совпадение по ИНН без размножения строк. 1 190 422 компании привязаны к ближайшему НП своего региона в 5 км. Адрес регистрации не устанавливает расположение производства | [интеграция](../work/data-audit-2026-11-07/integration-evidence.json) |
| Освещённость | implemented | Исходные значения в точках 155 412 НП за 2023/2024; карта региональных средних и таблицы НП. Ноль не равен отсутствию деятельности | [frontend](../frontend/atlas/README.md) |
| Сезоны и расписания | implemented | 18 записей девяти зимников Югры за два сезона; проверка даты и массы. Календарь КАП по дням/интервалам/отдельным датам. Круглогодичная связь — явно обозначенное допущение; альтернативные маршруты и эффект на Hansen не рассчитаны | [сезонная модель](../frontend/atlas/lib/additional-model.ts) |
| Индексы | code implemented; results unavailable | В коде Hansen, Harris/Remoteness, рынки за 1/2/4 ч, адаптация ARIA, OECD remote, приближение RAI, время до центра, сезонный разрыв/зависимость, Gini/Theil/Palma. `public/indices.json` пуст; `data/casechamp.duckdb` и транспортный граф отсутствуют. Экономическая доступность: `missing_transport_graph`. Карточки РФ — историческая сводка, не новый расчёт | [формулы](../docs/indices.md), [экспорт](../frontend/atlas/public/indices.json), [аудит](../docs/data-audit-2026-11-07.md) |
| Проверки интеграции | passed in previous implementation | 4 Python + 3 Node теста, TypeScript, production build; Chrome: регион, отрасль, поиск НП, масса/сценарий, календарь. Мобильная проверка отдельно не подтверждена | [результат](../work/data-audit-2026-11-07/integration-evidence.json) |
| Публикация сайта | not deployed | GitHub push выполнен. Отправку в закрытый Sites заблокировал auto-review; отдельного подтверждения публикации в Sites не получено. Не считать Git push размещением работающего сайта | [сессия](SESSION.md) |

## Coverage of A2 subtopics

Труднодоступные территории — наиболее проработанная подтема: данные и интерфейс готовы, последствия изменения сообщения ещё не рассчитаны. Межрегиональная — частично: модель в коде, текущих результатов нет. Агломерационная и глобальная — не закрыты; наличие отдельных исходников не означает готовую модель.

Главное требование А2 «понятный индекс → сравнение территорий → эффект возможного решения» выполнено частично. Для следующего шага нужны восстановление графа, исправления сезонности/направлений/ожидания/списка центров и проверенный сценарий одного объекта. Медицинская доступность требует реальных площадок и услуг больниц; грузопоток, рост ВРП и окупаемость — отдельных наблюдений и моделей. Эти результаты не обещаны как существующие.

## Historical facts — research branch, 2026-11-06

Следующая таблица сохранена как история. Ссылки на `brief/`, старые `datasets/` и `work/eda/` могут отсутствовать в текущей ветке; соответствующие материалы доступны в `chore/project-research` (например, `git show chore/project-research:docs/A2_citations.md`). Старые статусы и численности не заменяют текущий аудит.


| Topic | Status | Current fact | Evidence |
|---|---|---|---|
| Brief, 2026-11-06 | implemented | Supplied task preserved verbatim; requirements R01–R18 extracted; no scoring weights supplied | [source](../brief/sources/2026-11-06-task.txt), [requirements](../brief/requirements.md) |
| Deliverables, 2026-11-06 | verified against supplied text | Passport and artifacts by 10 November, 23:59; updated passport, 5–8 slides, speech up to 5 minutes and roadmap for 13 November | [submission rules](../brief/PLATFORM.md) |
| AI, 2026-11-06 | verified against supplied text | AI use and validation must be shown; AI-created materials must be attached | [R12 and R18](../brief/requirements.md) |
| Presentation excerpts, 2026-11-06 | implemented; copy verified | A2_citations.md copied from Downloads; passport length, artifact details and four unweighted expert criteria recorded; original slides not checked | [excerpts](../docs/A2_citations.md), [requirements](../brief/requirements.md) |
| Opening transcript, 2026-11-06 | implemented; copy verified | User-described opening speech copied unchanged from Desktop; audio not checked | [transcript](../docs/исаева.txt), [source record](../brief/sources/README.md) |
| Data acquisition, 2026-11-06 | implemented; verified | All 38 source rows accounted: 14 downloaded, 12 partial, 9 blocked, GAR deferred for disk, Open-Meteo needs parameters, OSM excluded by user; 185 local files, about 391 MiB | [catalog](../datasets/README.md), [coverage](../datasets/COVERAGE.md), [manifest](../datasets/manifest.json) |
| Data inventory | implemented | Original source table preserved; acquisition results and actual source limitations are recorded in datasets/; official organizer catalog link still absent | [inventory](../docs/istochniki_dannyh.md) |
| Git, 2026-11-06 | verified | Publication branch chore/project-research based on existing origin/main 5c81182; origin GoatWhistle/casechamp; all nonignored work prepared for publication, dataset raw/derived local | `git remote -v`, `git ls-remote --symref origin HEAD` |
| EDA, 2026-11-06 | implemented; verified | Computed city accessibility/scenario, municipal cohorts, regional bus intensities and geometric airport distances. City sample covers 52.59% of source census population; 2024 municipal paired cohort 1455. Earlier candidates; now economic-connectivity direction takes priority | [analysis](../work/eda/README.md), [checks](../work/eda/validate.py) |
| Economic direction, 2026-11-06 | user requested; framework proposed | GRP, development, criticality and traffic are the priority; economic inputs cover 85 regions in 2023; additional Kuzbass traffic 45 records found, period/5 inconsistencies require validation | [concept](../work/research/economic-connectivity.md), [traffic](../datasets/additional/traffic-counts-kuzbass/README.md) |
| Product choices | pending | Goal, territories, formula, scenarios and AI role are undecided | [questions](open-questions.md) |

## Pointers

- [Текущий аудит и ограничения](../docs/data-audit-2026-11-07.md)
- [Текущий атлас и запуск](../frontend/atlas/README.md)
- [Каталог дополнительных данных](../datasets/additional/README.md)

- [Session](SESSION.md)
- [Open questions](open-questions.md)
- Historical organizer materials: `chore/project-research:brief/README.md`
- Historical working artifacts: `chore/project-research:work/README.md`
- Historical product documentation: `chore/project-research:docs/README.md`
