# Парадигма Михаила Погосяна: первичные источники

## Universal bottleneck and development workflow, 2026-11-12

User: «вот нужно это всё подсвечивать».
User: «вообще переносимость на все регионы».
The user reaffirmed the earlier sequence: inspect accessibility and load, identify an
improvement, screen a straight graph connection, adapt promising connections to landscape,
then recalculate using the resulting geometry and road profile. Stavropol is an example,
not a hardcoded scope. This section is a proposed implementation contract, not completed UI.

Use one experiment module shared by map and agent. Its interface accepts evaluation scope
(pair, region, national), a versioned graph/demand baseline and bounded intervention limits;
it returns a persisted job/result ID, progress, coverage, diagnosed corridors, map geometry
and comparable variants. Internal data preparation, assignment, candidate search, terrain
search and summarization stay behind that interface. Reuse existing calculation/status
interfaces where compatible rather than expanding the initial agent tool list.

Distinguish the evaluated population, candidate work area and routing/demand coverage.
Regional boundaries must not clip routes. Include external destinations and explicitly
modeled cross-border/transit demand; missing transit is a coverage limitation. National
search screens overlapping local areas with common assumptions, deduplicates candidates
and verifies a shortlist. It must not promise an exhaustive national optimum. Every region
uses the same rules; missing road, population or terrain inputs produce explicit partial
coverage, not a silent successful zero or a claim that every region is already supported.

Diagnose separate problem types: conditional capacity overload and delay; inefficient
connections/large detours; fragile dependence on a corridor. Aggregate adjacent graph edges
into meaningful corridors before ranking and displaying them. An overloaded directed edge
count is not a count of independent bottlenecks. Show contributing routes and settlements,
assumption provenance and coverage. Prioritize verified intervention effects on travel time,
accessibility and affected population separately; do not invent a weighted composite score.
A rural access deficit can matter without heavy traffic. A Hansen score is not a congestion
measurement. Keep an unchanged normalization/reference when comparing scenario indices.

For each eligible corridor, compare bounded capacity upgrades, short connectors and bypasses.
Attach proposed connections to validated graph anchors; screen direct geometry using a declared
speed/profile. A straight connection is optimistic geometric screening, not a guaranteed upper
bound on network benefit once congestion and route choice interact. Hold the same OD demand
and time period across baseline, direct and terrain variants. Expose solver convergence,
unreachable demand, harmful results and displaced congestion. A portfolio needs a joint rerun.

Adapt only promising direct links. Load obstacle features and elevation tiles for their search
corridors on demand; cache source versions. OSM obstacle geometry and Copernicus GLO-30 are
proposed sources. GLO-30 is a surface model including vegetation/buildings, not a surveyed bare
earth model. Geometric crossing does not create a junction. Validate connection access, grades,
length, barriers and proposed structures. Missing legal/environmental layers stay unknown.
If no permissible alignment exists, reject the proposal rather than relaxing limits silently.
Recalculate with segment length, slope/profile assumptions and explicit bridge/tunnel choices.
This is preliminary corridor assessment, not engineering or investment approval.

Map design: a single problem layer shows the selected problem metric and provenance; selection
emphasizes the affected corridor and relevant connections, fading unrelated roads. Display the
direct proposal as dashed geometry and the terrain variant as solid geometry with explicit
labels, so meaning does not rely on color alone. Reuse existing design tokens. A compact
comparison has three rows: baseline, direct connection, terrain alignment. Columns include
route time, conditional load/overload, accessibility change and new road length. Do not conflate
regional Hansen and pair connectivity scores. Agent explains the same saved result and gives
one primary consequence plus the proposed remedy. It does not generate traffic statistics.

Acceptance cases: multiple regions with unchanged code; route crossing a region boundary;
pair/national scope; rural low-flow access deficit; shared-corridor aggregation; absent terrain;
no feasible project; unchanged demand across variants; a new overload after intervention;
non-converged assignment; package benefit recomputed jointly. UI and agent share result IDs.

Local inspection found untracked etl/synthetic_traffic and existing reports under
data/additional/synthetic-traffic/nevinnomyssk-comparison-v2/. The inspected report covers a
clipped snapshot with 157 settlements aggregated to 30 zones, not the whole Stavropol region;
its source explicitly omits inferred external transit. It compares capacity/speed changes,
not terrain-adapted new roads. No new experiment, product-code edit, paid call, commit or push
was performed in this discussion. Source checkpoint: feat/transport-scenarios-update, 986ae0f.

Primary terrain references rechecked 2026-11-12:
https://wiki.openstreetmap.org/wiki/Key:ele
https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM

## Follow-up: visual proposal of new road alignments, 2026-11-12

User clarified the sequence: select improvements from accessibility/load, screen a
straight hypothetical graph connection, adapt promising links to landscape, recalculate
using the resulting alignment. Recalculation should include speed/profile and common-demand
assignment, not length alone. OSM supplies mapped land/water/building features but no
continuous elevation surface; ele tags are sparse object attributes. Proposed additional
input: Copernicus GLO-30, global ~30 m DSM including vegetation/buildings, adequate for
initial corridor screening rather than engineering approval. Acquire only candidate-area
tiles and parse OSM obstacle geometries separately from the existing routing graph.
Sources: https://wiki.openstreetmap.org/wiki/Key:ele ,
https://wiki.openstreetmap.org/wiki/Key:natural ,
https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM

Design discussion only; no implementation or model evaluation. Proposed input to a
vision-capable model: immutable local map snapshot, readable road graph, highlighted
bottleneck with computed explanation, labeled eligible connection anchors, barriers,
scale and allowed intervention bounds. Supply a broader overview when needed.
Model returns anchor IDs and an approximate polyline in normalized image coordinates;
application converts points using the exact snapshot camera and image-to-map scaling.
MapLibre Map.unproject maps viewport pixels to geographic coordinates:
https://maplibre.org/maplibre-gl-js/docs/API/classes/Map/#unproject
Snapshot identity prevents conversion against a later camera state; resizing/cropping
and device pixel ratio must be accounted for. Geometry is a proposal, not surveyed precision.
Endpoints must attach to eligible real graph locations; intermediate road crossings do
not automatically create junctions. Do not snap the entire new road onto existing roads.
Validate length, access, water/terrain/land constraints and grade separation, estimate
time from length/profile, add a scenario edge/path and recalculate comparable outcomes.
Unknown barrier/terrain layers remain unknown. Traffic relief requires common fixed
demand and joint assignment; centrality or closure impact alone is not observed congestion.
Suggested bounded feedback loop: propose a few alternatives, render, return validation
and measured scenario effects, then permit a small number of revisions. The existing
two-node add_connection method is a basis for an abstract scenario edge; it does not
establish arbitrary-polyline buildability, intermediate connections or traffic relief.

Проверено 12 ноября 2026 года. Исследование для адаптации Plexus. Это реконструкция публично заявленного подхода, не утверждение о личных предпочтениях или обещание положительной оценки.

## 1. Интервью «Стратегия связанности»

Источник: https://oblako.mai.ru/articles/item.php?ID=167857 . Журнал МАИ «Облако», интервью Погосяна. Дата веб-публикации не подтверждена. Текст относится к раннему периоду работы совета по связанности; не выдавать за новое выступление.

Наблюдение: он определяет связанность через своевременное, экономически эффективное перемещение людей, грузов и информации и согласованную работу видов транспорта. Подчёркивает баланс социально-экономического развития и инфраструктуры. Среди результатов называет доступ к работе, бизнесу, образованию и культуре. Разделяет задачи длинных малонаселённых маршрутов и городских агломераций, где критична оптимизация потоков при ограничении пропускной способности. При описании гейтового подхода начинает с конечного эффекта проекта и его места в общей структуре.

Вывод для продукта: начинать с неудовлетворённой потребности и последствий, затем выбирать вмешательство. Дорога, рейс, пересадка или организация потока являются конкурирующими средствами достижения результата. Объяснять индекс через доступные возможности и утраченные связи.

## 2. Статья Погосяна с соавторами, «Вестник РАН», 2019

Источник: https://journals.eco-vector.com/0869-5873/article/view/12579 . М.А. Погосян, Д.Ю. Стрелец, В.Г. Владимирова. «Связанность территории Российской Федерации: от постановки комплексных задач к формированию комплексных научно-технических проектов». Том 89, №5, с.489–495, опубликована 6 мая 2019. DOI 10.31857/S0869-5873895489-495.

Наблюдение из авторской аннотации: подход идёт от актуальных комплексных социально-экономических задач к исследованиям, научно-техническим проектам и мерам политики. Типы связанности различаются социальными, экономическими и управленческими задачами. Поэтапный отбор предусматривает коррекцию программы и коммуникацию с заказчиками.

Вывод для продукта: предъявить одного конкретного заказчика, измеримый результат и этап проверки на реальной территории. Показывать основания приоритизации проектов, а не только ранжировать территории.

## 3. Пленарная сессия «Связанность территорий и освоение пространства», 9 декабря 2021

Источник: https://mai.ru/press/news/detail.php?ID=162224 . Официальная публикация МАИ, 9 декабря 2021.

Наблюдение: Погосян связывает направление с внутренней мобильностью и доступностью, интеграцией в международные коридоры и развитием экономики. Среди проектов выделены комплексное прогнозирование и моделирование для планирования территорий, интеллектуальная инфраструктура и мультимодальные системы. Критерии результата включают физическую и экономическую доступность, безопасность, своевременность и эффективность перевозок. Отдельно названы агломерации и малонаселённые труднодоступные территории.

Вывод для продукта: сравнивать пространственное распределение выигрыша и потерь, учитывать удалённые поселения отдельно от среднего по региону. Для мультимодальности нужны фактические расписания, пересадки и цены, иначе это лишь сценарий.

## 4. Портал приоритета «Связанность территории»

Источник: https://sntr.mai.ru/ . Дата страницы не указана; это описание программы, не отдельное личное высказывание Погосяна. На портале его обращение и материалы совета.

Наблюдение: различаются социальное, экономическое и управленческое измерения; глобальный, межрегиональный и внутрирегиональный масштабы. Цели включают преодоление диспропорций, доступность услуг населению, конкурентоспособность грузовых перевозок, безопасность и энергоэффективность. Комплексное прогнозирование и моделирование вынесено в отдельное направление.

Вывод для продукта: три понятных вопроса руководителя — кому недоступны возможности, где система уязвима, какое изменение даёт лучший результат при ограниченных ресурсах. Один агрегат следует раскрывать через людей, время, деньги и устойчивость; приоритет социально необходимой связи нельзя автоматически обнулять низким трафиком.

## Надёжность просмотра

Первичные страницы обнаружены поиском; поисковый инструмент вернул содержательные тексты интервью, аннотации и новости. Прямое open для части страниц МАИ вернуло timeout/cache miss; Основной агент отдельно прочитал полный HTML-текст статьи 2019 года на сайте издателя. PDF не проверялся. Утверждения об остальных материалах ограничены полученным текстом и индексированными фрагментами. Действующая должность и текущий состав совета отдельно не исследовались.


## Предложение для Plexus

Предложение, не утверждённая реализация. Рабочая гипотеза: инструмент заинтересует
эксперта по пространственному развитию, если соединяет потребность территории,
конкретный разрыв связи и проверяемый эффект вмешательства.

1. Основной вопрос: где сеть перестаёт обеспечивать нужные перемещения и что это исправит.
   Пользователь: руководитель транспортного развития региона, с подготовкой расчёта аналитиком.
   Выбор: какой критический коридор и какое вмешательство отправить на детальную проработку.
2. Первый экран: доступность, критические зависимости, изменения относительно прошлого
   сопоставимого снимка. Карта сопровождается коротким объяснением и следующим действием.
   История состояний и автоматические уведомления пока являются предложением.
3. Hansen оставить обзором потенциальной доступности. Показать собственный и внешний
   вклад отдельно, без незаметного изменения определения. Потери отдельных направлений,
   время и охват жителей раскрывать рядом. Малое изменение среднего не снимает локальную проблему.
4. Трафик описывать через спрос, способность и последствия переноса нагрузки.
   Высокая интенсивность может означать отсутствие альтернатив. Малая интенсивность не
   отменяет социальной и стратегической необходимости связи. Жители пунктов не равны потоку.
5. Сравнивать открытую сеть, закрытие и то же закрытие с вмешательствами А/Б на одном
   графе, одном наборе направлений и одинаковом спросе. Показывать восстановленные связи,
   время и условную нагрузку. Это требует общего контракта эксперимента, сейчас нельзя
   автоматически считать существующие раздельные расчёты сопоставимыми вариантами.
6. Для авиационного развития формулировать транспортную задачу: откуда, куда, что
   перевозится, с какой регулярностью и по какой доступной цене. Затем сравнивать средства.
   Рабочий дорожный стресс-тест сейчас не учитывает замену на ЖД или авиацию.
7. Для мониторинга нужны сопоставимые временные снимки фактических наблюдений, даты,
   источники и события. Изменение данных/метода отделять от изменения состояния сети.
   Сценарные допущения о нагрузке показывать компактно отдельно от наблюдаемого трафика.

Ближайший приоритет: один законченный дорожный эксперимент с двумя альтернативами,
компактной таблицей и проверенным выводом. Затем история состояний, затем проверка
наблюдениями и один мультимодальный пилот. Строительные затраты и спрос нужны для
инвестиционного выбора; текущая оценка доступности сама по себе окупаемость не устанавливает.

## Локальная основа и границы

Проверены документы: docs/indices.md, docs/road-stress.md, docs/traffic-diversion.md,
docs/road-capacity.md, work/hackathon-decision-plan.md,
work/agent-business-brief/README.md, work/table-tools/README.md, presentation/SPEECH.md.
Это анализ реализации по документации, без новых запусков приложения или расчётов.
Национальный дорожный стресс использует фиксированные веса; модель переноса нагрузки
работает отдельно для 2–4 пунктов с независимыми экспериментами по парам.
История сохранённых расчётов не равна истории наблюдаемого состояния транспортной сети.
Код продукта, презентация и работающие процессы в этой задаче не изменялись.


## Follow-up: existing versus required

User: «что уже есть и что нам нужно чтобы закрыть эту хотелку».
Existing: regional atlas/Hansen, road criticality and improvement candidates, closures,
named delayed/lost connections and detours, separate conditional traffic diversion,
rail/air link edits at regional index level, saved calculations, map and agent.
Required for a coherent decision workflow: common experiment scope and inherited disruptions,
compact consequence/intervention comparison and one validated end-to-end decision case.
Required for actual monitoring: timestamped observed flow/service/closure inputs,
repeatable ingestion, comparable network-state snapshots and changes/alerts.
Historical calculation storage does not satisfy that monitoring requirement.
No implementation requested or performed in this follow-up; documentation reviewed only.


## User correction: network development first

User: «да, но ведь потеря маршрута какая то слишком узкая задача. Нужно добавлять пути».
This supersedes the recommendation to make disruption recovery the primary scenario.
Primary product scenario: identify missing/inefficient connections, propose new links or
service routes, compare their accessibility gains and capacity effects on a common baseline.
Closures become a secondary resilience check for proposed network development.
Code inspection confirms RoadGraphService.add_connection supports two distinct graph
nodes and a supplied travel time. RoadEvaluation improvement mode only accelerates an
existing OSM way; it does not discover new connections. Required proposed additions:
candidate generation for missing links; scenario portfolios; fixed-scope route/accessibility
comparison; capacity/demand assessment appropriate to each transport mode. A hypothetical
edge is not an engineering-approved alignment. No implementation performed.


## Bounded connectivity improvement search: proposed algorithm

User: «ну вообще надо продумать связанности. Какие то не сильно глобальные изменения и скрипт как их искать вообще. А если человек не в регионе а в паре хчоет. А если просто по всей рф. Но при это раскинуть трассу 10 полос между москвой и камчаткой нельзя)».
Design only; no new search script or product implementation has been created yet.

Separate intervention eligibility from evaluation scope. A pair evaluates its requested
trips on the full relevant network; a region selects origin population but permits routes
and cross-border candidate works outside its boundary; national search enumerates bounded
local projects in spatial tiles with overlap, then assesses cross-tile/transit effects.
Never clip the routing network to the candidate-generation tile or administrative region.

Inputs: pair/region/national demand scope; explicit destinations and transport mode;
immutable graph/method snapshot; permitted intervention catalogue; physical size limits;
optional costs and observed or assumed traffic; candidate verification budget.
No inferred traffic from settlement population. A pair does not become a regional score.

Initial catalogue: improve a contiguous existing-road corridor with a justified profile;
short local connection between eligible existing junctions; short capacity expansion only
with a load model; later service changes between existing transport facilities.
Example configurable search policy, not standards: new connector <=5 km, upgrade <=30 km,
capacity expansion <=10 km and at most one extra lane per direction / four total lanes.
An absolute project-size bound remains binding for every evaluation scope.
No unrestricted speed multiplier, free crossing, virtual motorway or arbitrary edge time.
Buildability/terrain/water/land and connection-access restrictions must be checked. If those
layers are absent, new connector candidates are explicitly unverified hypotheses and do not
enter the same recommendation class as reviewed existing-corridor interventions.

Candidate generation: group OSM segments into bounded contiguous road works; shortlist low
performance corridors on relevant paths; use nearby eligible road endpoints/junctions for
short-connection candidates; check detour significance, existing links, access restrictions,
possible map omissions and barriers; deduplicate parallel segments and neighboring tiles.
Nearby geographic nodes alone are insufficient: bridge decks and roads below can be close.
Disconnected graph components may reflect missing data and go to a separate data-audit queue.

Pair screening: compute baseline distance arrays from A and B on the existing undirected
nonnegative graph. For one proposed u-v edge of time w, exact fixed-weight pair time is
min(d(A,B), d(A,u)+w+d(v,B), d(A,v)+w+d(u,B)). This formula is not a capacity/queue model.
Bounded corridor profile changes can use optimistic bounds for screening, then full rerouting.
Regional/national screening: use existing accessibility caches and a fixed, recorded origin
sample for initial ordering; spatial index for nearby candidates avoids an all-node-pairs scan.
Fully verify a bounded shortlist against the declared full evaluation population. National
screening is heuristic and may miss projects; record candidates considered, sample, omissions,
truncation, graph version and final verification coverage. No claim of a global optimum.

Results use separate objective tracks: restored/new access, journey-time reduction, reserve
connectivity, capacity effects when supported. Keep absolute and relative changes, physical
project size, affected places and verification status. No unsupported composite of minutes,
population and guessed costs. Compare like work types or expose Pareto trade-offs; with no
cost data do not call gain per km an economic optimum. Return no eligible improvement when
none meets constraints. Never relax geography or lane limits silently.

Top projects are standalone baseline comparisons, not additive portfolio benefits. For a
package, apply each chosen project to a common scenario and recompute remaining marginal
benefits; combinations can interact and a greedy search is not a guaranteed optimum.
A long-distance disconnected road pair can legitimately produce no small road intervention;
existing-facility multimodal alternatives require a separate supported transport model.

Suggested implementation order: common limits and result contract; existing-corridor pair
search; regional/national reuse with spatial candidate screening; verified short connectors;
capacity assignment and multimodal service interventions. Unit checks should cover a huge
shortcut rejected by size, geographic crossing without interchange, zero-benefit lane increase
in free flow, benefit outside a region, no eligible solution and portfolio double counting.


## Synthetic traffic demand and relief assessment

User: «окей. Как мы можем эмулировать нагрузку ? чтоб считать разгрузку и тд ?».
Proposal only. Existing assign_diversion and loaded_pair were inspected; no model run or
implementation change performed. Existing independent-pair closure demand equals closed
corridor capacity times utilization. This must not be reused to regenerate demand for each
new infrastructure variant: otherwise added capacity changes the assumed demand itself.

Build one reproducible OD demand matrix for a declared time period and vehicle classes.
For a pair, use specified A-to-B demand and explicitly included surrounding trips/transit.
For a region, generate origin productions from population and declared trip-rate, car-mode,
occupancy and time-of-day assumptions; distribute interzonal productions among destination
attractors with a baseline travel-time deterrence function. Retain local intrazonal trips
outside intercity road loading, and separate unreachable demand. Population can proxy
attractiveness when employment/service data are missing but cannot establish observed flows.
Freight and long-distance demand require separate assumptions; avoid inventing truck flows
from resident populations. National search needs coarser transport zones and a sparse demand
matrix, not all settlement pairs. Include external trips crossing analysis boundaries.

Scale the SAME matrix into low/base/high demand cases (illustrative 0.7/1.0/1.3, not measured
levels). Fix demand, units, period and generation parameters between baseline and project
variants. Do not create uniform per-link 50% background in addition to overlapping OD flows.
Demand is held fixed for the initial comparative experiment; induced demand is a separate
long-term scenario, not an implicit recalculation after an improvement.

Assign all OD pairs jointly on a directed network with directional/shared-lane capacities,
using iterative shortest-path assignment and monotone volume-delay functions. MSA is one
simple initial solver; a recorded equilibrium-gap tolerance and iteration budget determine
whether the result is converged. Demand on common edges is aggregated before recomputing
travel cost. Capacity does not itself create demand. Recover free-flow times before applying
assignment delays to avoid adding an existing delay twice. Current routing is undirected;
directional conversion/data validation is an explicit implementation task.

Static assignment provides conditional flows, volume/capacity ratios and travel delays.
Assigned volume above capacity represents overload demand and is not completed throughput.
Queue lengths and time-dependent discharge need a separate finite-period network-loading
model with flow conservation and upstream constraints; current independent pair queues cannot
simply be added across a network. For a first version, show static overload and delays, then
add time-sliced point queues for a bounded corridor if actual queues are required. Distinguish
point queues from spatial spillback; unknown disconnected demand never becomes zero travel time.

Compare total vehicle-hours for the same demand and period, OD journey times, edge volume
changes, overload ratios, and newly loaded bottlenecks; report residual unserved demand and
solver convergence. Keep PCU capacity units separate from physical vehicle-hours, and use
class-specific counts when computing vehicle-hours. Repeat each project for all load cases.
No forced positive effect: retain null, harmful and demand-sensitive results.

Primary references checked 2026-11-12:
- AequilibraE 1.6.0 assignment procedure: https://www.aequilibrae.com/docs/python/v1.6.0/traffic_assignment/assignment_procedures.html
- FHWA Traffic Analysis Toolbox XIV, base model/OD estimation: https://ops.fhwa.dot.gov/publications/fhwahop13015/sec6.htm
- FHWA calibration/validation distinction: https://ops.fhwa.dot.gov/publications/fhwahop13015/sec8.htm
The proposal creates scenario comparisons; observed traffic claims require calibration and
validation on separate measurements. No actual traffic levels or congestion relief measured.


## Preserved scope checkpoint, 2026-11-12

Reaffirmed direct-link screening, terrain adaptation and comparable recalculation.
[Proposed shared map/agent workflow and acceptance cases](../work/pogosyan-product-framing.md).
Discussion only; no product edits or new experiments. Local synthetic-traffic reports cover
a clipped Nevinnomyssk-area snapshot, not all Stavropol. Next: implement the shared experiment
contract and corridor diagnostics without region-specific code; preserve existing dirty work.
Branch feat/transport-scenarios-update, HEAD986ae0f. No commit/push or paid calls.
