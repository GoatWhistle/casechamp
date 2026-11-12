# Session state

## Explicit user instructions

2026-11-06:

> возьми шаблон https://github.com/GoatWhistle/template и поставь его сюда, только тот мд с табличкой что уже есть закинь в докс

<!-- plane-workspace-insights: explicit invocation only -->
Use Plane Workspace Insights, its six plane-* skills, and its Plane MCP tools only when the user explicitly invokes this plugin by name, selects it, invokes a $plane-* skill, or explicitly asks to use the Plane plugin. Mentions of tasks, projects, reports, dashboards, or Plane data alone do not activate this plugin. Once explicitly invoked, continue within that task's authorized scope. This rule applies in every working directory.
<!-- /plane-workspace-insights -->


2026-11-06:

> теперь задание хакатона добавим.

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

2026-11-08:

> Resume this session with:
> claude --resume b50b925b-d840-4b2d-9ed2-b7d8029382b1 вот сессия старая клода доделай этот хтмл файл щас плохо . надпись плексус хуйня она страшная из-за шрифта  и цветов которые отличаются от дизайн системы не отходи от нее . также анимация с картой очень долная используя все скилы подумай какую другую анимацию можно сделать тчобы она было не долгаи и какую сделать анимацию построения надписи

> ты можешь анимацию отрисовки надписи оставить как была раньше . чтобы буквы красиво появлялись

2026-11-08:

> прорисовка букв очень лагает . и просто анимация говно зачем месяца эти и прочее подумай абстрагируясь какую можно красивую анимацю сделать на главную страницу

2026-11-08:

> как это работает кнопку убери . можешь чуть украсить как надпись появляется и эту анимацию справо как то украисить подумай и переплетения нечеткие и не понятно зачем нужно это

2026-11-08:

> пусть шарики все вермя катаются

> и добавь на фон чтото а то много пустоты белой . фон может какой то с картой может нимацию с картой где много путей ъуй пойми какой и там наш сервис все делает понтяным

> проверь чтобы совпдала с дизайн системой которая в корне проекта

2026-11-08:

> карта каличная очень бледная и кривая может еще чтото на фон поставить подумай хорошо пожалуйста

2026-11-08:

> куда эти линии уходят непонятно . сделай чтобы не было в пустоту

2026-11-08:

> эти круги вылазеют за экран ну просто пиздец еще давай какой то фон ты не можешь сделать на фон карту чтобы она полностью помещалась и чтобы маршруты по этой карте шли через наш этот икс


2026-11-08, prototype and integration instructions:

> сделай обновленный хтмл в корень проекта макет где будут реализованы все предложения клода

> в будущем я скажу тебе что ты итогвые две хтмл взял как образец и реализовал в проекте в ветке фронтенд и потмо сделал комиты и  пуши только убери чтобы в комитах хтмл созданные в корне не было . но не удаляй . пока просто план закрепи у себя когда сесси закончат я скажу делай

2026-11-08, integration authorization:

> все хтмльки готовы начинай работу токо не делай проверки под мобильные устройства

> не добавляй ничего не бек если  . оставь токо то что есть

2026-11-08, local preview before publication:

> пока не пуш залей на локалхост 8080 чтобы я протыкал

2026-11-08, home review:

> повторить анимацию кнопку с главной страницы убери

2026-11-08, map review and commit batching:

> почему открыть атлас открывает какое то странное меню надо чтобы как раньеш до двух комитов отрывалась большая карта

> пока не делай комитов пусть все мои коменты потом сделаешь одним комитом

2026-11-08, interaction review:

> когда в источниках переключаешь вкладки на секунду на пол экрана черточка . когда в методике по квадратикам ведешь надо чтобы походу этого менялась надпись . на странице региона пролистывается непонятно как не получается проилстать до конца.  зачем когда нажимаем на регион остаются связи всей россии надо чтобы там писались связи городов региона которые щас в карточке

2026-11-08, publication authorization:

> закомить и запушь все комиты

2026-11-10:

> Давай используя pydantic ai v2, сделай мини агента и чат справа от карты, в который можно писать промпт. Пиши сразу стрим. Нужен шлюз с codex agents sdk в responses api амодели, юзай gpt 6.1 sol. Используй мою авторизацию

> так, фронт чатика спизди примерно от сюда https://github.com/GoatWhistle/rwb

> нормализацию с тех чатов тоже стырь. Графики, таблички, пункты

> (H_i=\sum_j M_j f(c_{ij})), где (M_j) — размер рынка в пункте назначения, (c_{ij}) — затраты на поездку, а (f) уменьшает вклад это тоже надо нормализовать. Давай дальше управление картой и крутые зумы сделаем

> дай возможность пересчитывать. Если мы вытащим все графы в постгрю, станет же лучше работать ? и на ходу сможем считать всё ?

> запуль сюда данные графа из гита посмтоир сам где валяется

2026-11-10, rail/air source research:

> ищи субагентами по ВСЕМ РЕГИОНам. ГДЕ НЕТУ ЩАС ЖД И АВИА


### Additional user instructions carried forward

> зайди в контекст проекта /Users/kaifarikman/Downloads/2\ кейс.pdf /Users/kaifarikman/Downloads/2_Транспортная\ связность.pdf вот тут тебе ТЗ. посмотри что лежит в каждой из веток. нужно это все дело корректно смерджить

> тогда запушь это дело в мейн щас, тупо туда влей и остальные ветки на remote и local удали. все будем делать в мейне

> цель - понять, корректно мы все делаем или нет. у тебя есть ТЗ. осознай что мы сдлеали, что нет, где минусы, где плюсы и что осталось. какие риски по проекту

> твоя цель - выполнить все то, что я тебе описал в этом плане. не подведи. тут важный проект. всегда поступай по рекомендации брат. файл - work/project-plan.md , работой

> стой друг

> исправил доку. осознай новые изменения

> пока что забей, поставь пропуски

> зайди в домен. изучи ТЗ , требования /Users/kaifarikman/Downloads/2\ кейс.pdf /Users/kaifarikman/Downloads/2_Транспортная\ связность.pdf и посмотри что уже сейчас готово и что покрывается

> давай короче все изменения которые были(все коммиты) перенесем в другую ветку, на нее переключимся и там уже пойдем работать, тестировать и пробовать

> давай , делай

> все теперь это запушь дело всё и  скажи куда запушил

> втащи сюда последние изменения с гита, как фронт так и feat/model-validation. Но не затри данные новые

> найди такие же датасеты для всех регионов

> запушь в новую ветку

> frontend/claude-trans.txt продолжи че там делали, но без тестов

> коммит и выкатывай на стенд case.vm

> ssh main.home-1.serv

> запусти субагентов и дособери

> подключай к стенду

> давай запушим это

> спуль ее и затри то что мы меняли

> тут всё еще есть пилот тывы ? мы должны всё уже поддерживать. Предложи сценарии в которых агента можно использовать

> сделай чтобы на локалке и граф отрисовывался и чтобы инструмент сранвения был и пересчета индекса. ВОозможно какие то вопросы по графц

> не надо, юзай только эти данные, не костыль

> ПОДКЛЮЧАЙ СУКА

> а почему при приблежение у нас пропадают связи графа ? + что за расчёт ? перерасчет при добавление чего то ? мы можем уже добавить через агента тул ( желатлеьно чтобы перерасчет шёл только diff ом, чтобы моментально ) и выводить там какой то эффект на индекс и эффект денежный условно

> и почему вот есть серым дорога, но граф синий не всю ее покрывает ? это как раз общественный транспорт ? или что это

> давай посчитаем заранее и будем держать всё и только дифы быстро считать

> смрежи с тем что в ветке удалённой лежит

> В этой копии есть готовые индексы, но отсутствуют data/graph_ru/ u data/casechamp duckdb с расчётным графом и матрицей времён. Где лежат эти артефакты или как подключиться к серверу с ними? это надо запушить в гит

> делай оба

> удали следы этого ограничения про тыву вообще везде

2026-11-10, local transport data update:

> ну добавляй блять на прод их

> здесь имеется ввиду локально актуализируй и добавь данные

2026-11-10, road rendering and storage:

> мы можем как то переписать упрощеннее рендер графаов свяжей дорог? чтобы оно быстрее рендерилось. А не как щас долго
> и очень пролагивает когда нажимаешь на регион
> продолжай
> можешь все датасеты свести к постгре чтобы быстрее искать или кликхаусу, смотря что будет быстрее здесь

2026-11-10, road graph completeness:

> Дособирай данные по графу дорог там, где ещё их нет. А то очень плохо терять индекс из за неналичия дорог!

> проверь все регионы

> да, в кликхаус заносятся и сносятся

> Да, удалить временные OSM-файлы

### User instructions retained from earlier status entries

User request: «прочти тз хакатона».

User: «поправь наслоения и уменьши этот островок»; «Ответы основаны на данных атласа убери это».

User: «Implement the plan.» Details and verification: work/road-analysis-implementation.md.

User: «доправь визуал тогда расчета, чтобы он прям в чате рисовался с анимашкой и зум был того где мы делаемся».

User: «делай и закинь в последний коммит». Integrated settlement picker and effect table with national graph, not remote endpoint-only approximation. Real UI12min connection completed with1275affected origins/top30rows. Backend176tests and frontendverify pass. Amend requested for latest local commit; no force-push. Details: work/scenario-form-integration.md.

User asks how incomplete roads affect the index (Komi example). Reviewed docs/indices.md, docs/limitations.md and etl/indices.py; no model changes. Current model cannot distinguish missing edges from real disconnection; coverage is reachability, not source completeness. Recommend explicit uncertainty and source validation before interpreting rankings/scenario gains. Komi completeness not audited. Branch feat/map-first-ui HEAD c82ab1e. Next if requested: audit Komi calculation graph versus rendered layer. Context budget exceeds SESSION target due to protected instructions; retained verbatim.

User: «посмотри на фронтенде, почему долго отрисовываются свзяи и граф дорог, как можно оптимизироваться ? может рисовать не сразу всё, а поступательно ?»

2026-11-10, complete database migration:

> теперь все данные лежат в кликхаус или мы все еще занимаемся маразмом и ходим в дак дб ?
> перетащи их в бд удали файлы исходные потом. Джсоны для скорости распарси в таблицы
> продумай индексы чтобы ускорить выводы все

2026-11-10, publication authorization:

> скомить все изменения и запушь их. Обязательно опубликуй данные

> Подтверждаю загрузку этих данных


### Additional retained instructions

> и добавь чаты, новые старые, аккуратно только как то
> напиши в отчете по чистой архитектуре. Что там есть умный ии агент. ЧТо там граф огромный
> и сделай в маркдаве
> прочти Шаблон паспорта проекта.docx и сделай такой но по нашему проекту. Задавай вопросы. Тут мы должны описывать только то что есть уже. НЕЛЬЗЯ ПИСАТЬ ЧТО МЫ ХОТИМ ДАЛЬШЕ
> Пиши туда Инструменты промышленной разработки. Python, Фреймворки для анализа данных, Матан, Алгоритмы и структуры данных. Основы сетевых технологий.
> Не было, это зачем? дай контекста и снова вопрос задай
> Оставь пустым, я докину ссылку на деплой
> Да, проверяли через интерфейс
> подними щас локальную версию в полном составе который щас есть и не трогай
> как убрать если я другой чат открыл уже. Плюс надо удалять чат уметь
> что не так

2026-11-11, additional data publication authorization:

> Да, добавить новые результаты

Approved plexus_accessibility.runs, results and frequencies in the same GitHub release.


### Additional retained instructions at publication closeout

> делай
> что ещё крутого и важного доавбить, посмотри как индекс поменялся распиши в чем его суть что и как показывает.
> оформи максимально красиво, можно табличкой приросты. Убери слопные длинные тире, стрелки, точки с запятой
> делай
> оставь В ОДНОМ ФАЙЛЕЕЕЕ БОЛЬШЕ НЕЛЬЗЯ!
> теперь отрендери это в пдф

## Configurable routing workers, 2026-11-11

> ну крч сделай чтобы до 20 воркеров могло быть и я мог задать это значение
> крч 48 потоков. Максимум

## Map-first UI polish, 2026-11-11

> в моих коммитах не должно быть меня, пушим от андрея и только от него, без контрибьюторства клода
> разрешаю пушить от имени андрея. пушь сам, без контрибьюторства клода, короче надо прям тебе ебашить, разрешаю пушить и коммитить, конвенции всего у тебя есть

## Latest user instructions, 2026-11-11

> не пуш ничего и не комить

> обнови репу полностью и удали все мои несохраненные измения и запусти последнюю ветку где фронт обновился ласт раз и подними проект обновелнный

The latest reset request supersedes older instructions to preserve local edits and root HTML.

## Current local runtime, 2026-11-11

Historical runtime: [record](../work/local-runtime-2026-11-11.md).

## Runtime questions, 2026-11-11

> чего не хватает чтобы полноценно протыкать проект

> мою авторизацию это что тебе апи ключ нужен или как

> я не понял в итоге что тебе скинуть чтоыб все заработало

> что такое новые связи обьясни и зачем вкладка расчет новых связей

## Source tabs and map legend, 2026-11-11

> исправляй в этой же ветке и комиты от лица андрея сейчас в вкладке источники я переходя по вкладкам тыкая туда там полоса на всю панель расширяется также доступность рынков на карте вот эта залупка маленькая надо чтобы ее можно было сужать расширять или вобще свернуть пусть она в кружок сворачивается с каким то символом котоырй по логике продукта подходит подумай какой сделать или омжет какой то общепринятиый

Completed implementation and checks: [map controls record](../work/screens/map-controls-fix.md).
Protected instruction history exceeds SESSION target and is preserved verbatim.

## Diagonal legend sizing, 2026-11-11

> надо чтобы можно было по диагонали двигать эту панельку

> Растягивать панель за угол

> и сужать

## Legend border interaction, 2026-11-11

> убери кнопку пусть я просто подводя к панели могу растянуть и убери черные надписи у кнопки сворачивания панели

Completed map-controls history and verification: work/screens/map-controls-fix.md.

## Frontend publication

> запуш


> а там что пушится паралельно


## Complete the map chat, 2026-11-11

> посмотри ласт сессию клода доделай что он сделал и если код фронта готов залей его на 8000

> просто любой другой порт выбери

> Нужно восстановить авторизацию провайдера на сервере, затем повторить запрос. мне так в чате ответили

> сделай чтобы заголовки чатов писались исходя из того что пишется в чате ну типо как в гпт чтобы было также

> убери надпись ответ готов также щас сообщения от нейронки щас не выделены просто как по полотну настрато можешь их в какую то рамочку сделать но чтоыб не сильно глаза портило .

> вкладка действия тоже нахуй не нужна убери и источники данные тоже . просто пусть это будет когда вот человек уже поулчил ответ и будет быстрое нажатие сообщений покажи источники и тогда этот ответ приходил

> как все что я написал в чате доделаешь и проверишь запушь закомить от лица андрея

Unified map chat and auth fix are published as Andrey in5aa8d1b/0612343 on feat/map-first-ui.
Runtime8080 is healthy;8000 belongs to MASP/modus. Details and limitations:
[chat workflow](../work/screens/chat-workflow.md).
Protected user instructions exceed the SESSION target and remain verbatim.

> смотри щас я когда источники попросил заголовок стал про источникик пусть он один раз делается и все .

> также я не могу чат листать вверх когда я попросил источник у чата

> еще пока я чат листая постоянно появляются белая пустота в нем . это не надо испрвь

Preserve command-scoped author/committer andreysk0304 <andreysk0304@yandex.ru>.
Limitations: full road rendering at1920 exceeded45s; /scenarios matrices remain unavailable.
Evidence, negative checks and runtime details are in the chat workflow record.


## Local launch on this machine, 2026-11-11

User: «подними проект»; correction: «Ветка последняя это мапс ui  чёт такое».
Branch feat/map-first-ui, HEAD 0c7cb89. Latest UI8080/API8000 and restored ClickHouse
are running; graph viewport and atlas HTTP checks pass. No commit/push. Runtime,
failed checks and limits: [record](../work/local-runtime-savelij-2026-11-11.md).
Protected instruction history exceeds SESSION budget and is preserved verbatim.

## Territorial indices research and separate plan

User instruction (verbatim):

> твоя задача поискать еще такие важные муниципальные, региональные или федеральные индексы и составить отдельный план

Scope corrected: legally grounded indicators only; [revised plan](../work/territorial-indices-plan.md), broad survey archived in work/research/. Nine normative measures plus separate approved methodologies; current-edition gaps explicit. Branch feat/map-first-ui,0c7cb89; no code changes. Next: verify legal versions and pilot inputs.

User clarification (verbatim):

> это то что регулируется по правовым актам, к примеру как в том примере что я скинул


User instruction (verbatim):

> только делай в отдельном ворктри

User instruction (verbatim):

> подними теперь с выполненным планои

Worktree /Users/savelij/projects/casechamp-normative-indices, docs/normative-indices-plan, base0c7cb89. Pilot UI8082/API8002 running; N01/N02/N05 model calculations and ClickHouse persistence implemented. Full plan remains open for legal/data verification and other transport models. Checks, failures, commands and next steps: [implementation record](../work/normative-implementation.md). No commit/push; main worktree preserved.


## Normative map integration, 2026-11-12

Active goal preserves the user request verbatim:

> image file: /Users/savelij/.codex/attachments/97be638b-1865-4031-a4e9-86f413d3780e/image-1.png  все должно быть тут. Выполни полностью /Users/savelij/projects/casechamp-normative-indices/work/normative-implementation.md и сделай адекватный и красивый UI/UX

Worktree docs/normative-indices-plan, HEAD0c7cb89; no commits/push. API8002 and UI8082 running. Main metric dropdown has14items, right panel/map replaces the separate normative screen; legacy route redirects. Five car criteria work,788real facility-profile records imported; latest assessment restores typed snapshots. N06 baseline85.1267%, N08baseline49.8839% lower bounds; both upper100% due incomplete inventory. Full plan remains open for response/walking/school bus/municipal conditions, current legal editions and entrance verification. OSM PBF acquired, pedestrian graph not built. Details and next steps: work/normative-implementation.md.

Current checks: frontend433tests/build/rules/lint pass, backend265unit tests/Ruff/mypy and2module integrations pass; desktop1440/1920 has0JS/axe issues. Full integration baseline still44pass/1fail from absent private analysis history. Whole-backend Ruff format check fails on pre-existing tests/unit/controller/test_chat.py:66; changed files formatted. No mobile/paid checks. Protected history exceeds SESSION target and is retained verbatim.


## Provenance checkpoint

Current: docs/normative-indices-plan, HEAD0c7cb89; separate worktree casechamp-normative-indices, UI8082/API8002 live, no commit/push. All9branches have physical models: N03 now requires an explicit saved speed/assumption and uses edge kilometres, with depot-to-call geometry and10/20min by call settlement type.9depots/2settlement contexts,1233unknown thresholds; all fire legal statusesunknown. N07:24local libraries,40/60by municipality,2sources/1233unknown thresholds; all legalunknown. Walking-v2 has41236references, clinical adult denominator unknown; mfc-33 excluded(16coords,88.075%lower model bound). normative-v3 freezes model, attachments, facilities, criteria and costs. Backend308unit,4prior+1newmodule integrations, Ruff/mypy pass; frontend437tests/36rules/build pass. Desktop1440fire input validation+real14node route:0JS/axe. Full plan remains open on legal editions, entrances, populations/catchments, territorial and operational transport evidence. Asked whether the team has departmental data; no reply yet. saved_at now replays exact UTC metadata time; legal card uses saved criterion, graph descriptor has a compact SHA256code. Audit work/audits/normative-completion-2026-11-12.md explicitly finds remaining N04/N09 conditional-rule code and data gates; Compose rerun unverified. Next: implement walking applicability matrix; research tasked to health_article in work/research/walking-conditional-rule-matrix.md. [Evidence/tasks](../work/normative-implementation.md), [prior archive](../work/normative-session-history-2026-11-12.md). Protected instructions exceed SESSION target and remain verbatim.


## Walking v4 checkpoint

Branch docs/normative-indices-plan@0c7cb89, separate worktree; no commit/push. Details: `work/normative-implementation.md` sections Условные школы и остановки v4 and following. UI8082/API8002 dev running (APIexec92162, PID77176). Isolated Compose UI8083/API8003, project plexus-normative-verify, external network casechamp_default, existing CH read/write own normative tables, independent cache volume; CHAT_ENABLED=false. Config/log/results in `.local/compose.normative-verify.yaml`, `.local/compose-normative-verify.log`, `.local/compose-normative-result.json`. Root original worktree unaffected.

Conditional code implemented: WalkingFacts strict validation before importer opens storage; six school/two stop rules, separate jurisdictions/transport limits, no universal500; exact admissible target selection, inventory-completeness guard for exceeded, measurement_graph_revision matches actual walking routing revision, per-closure scenario attestation. Non-regulated/not-applicable excluded from numeric denominator. Sparse shared rule_sets, typed raw fact snapshots and explicit Arrow column list. Modelv4; v3 physical route replay compatible. HTTP includes groups/reference and counters, private raw facts not exposed. Dataset facts empty intentionally. New UI rule disclosure and neutral excluded states, old saved rule-less result asks recalc.

345backendunit/232mypyfiles/Ruff,5moduleintegration,8ETLtests pass. Frontend440tests/36rules/types/Biome/build pass. ETL first run missing `etl` onPYTHONPATH failed collection; corrected `PYTHONPATH=etl:backend/src backend/.venv/bin/python -m pytest etl/tests -q` passed. Old untracked walking tag tests accidentally overwritten recovered from this session JSONL as test_walking_tags.py; all10cases preserved. UI first assertion expected wrong phrase; corrected. Axe initial N09 transient color-contrast during Disclosure opacity animation; repeat500ms after final click clean. No product CSS change needed.

Baselinev4 N04 run168cc269678a473cb4d1223fa809b01d:41236rows27577paths. N09 f7f431f6f9e94feb89daa4048fc89906:27578paths. Compose POSTN09 run98c9e0938c3344c4b7bb43866be2e424 exactlatest restore, replaces latest but samephysicaldata. Allunknown, groups1 with6/2checks. Desktop1440N04dev and1920N09Compose: JS/axe0, overflowfalse, 1844/1767pathnodes; screenshots /tmp/normative-conditional-N04-1440.png and N09-1920.png. No mobile/paid calls. Full previous integration failure private historical saved analysis still an honest known limitation.

Next: real departmental entrance/exit/catchment/population/service/calendar/vehicle data, confirm current legal editions. Existing unanswered data question stays pending; don't fabricate inputs. Full plan remains unfulfilled on these gates; goal active. Current Docker verification is images+existingDB, not restorefromscratch. No reason to re-run green checks absent new changes.


## Regional library checkpoint

Previous goalturn=progress (v4conditions+Compose). Currentturn=progress: official library catalogue index collected:26categories/66pages/481actualcardURLs and listing dates in work/research/library-directory-card-index.json (completed research and explanatory work/research/library-directory-extraction.md). This is publication inventory, not481confirmedfacilities. Full primary-body/address extraction across index remains next. Some cardreader cache ages up to1.6years, pages refreshedtoday; directlocalurllib30/curl20/IPv4connect5timeout. Do not invent HTML selectors or rawHTMLhashes.

Persistent reviewed facts datasets/normative-library-source-records.json (14Ketovo cardrecords,13addresses,4unreadURLs including5721). work/research/library-directory-ketovo-candidates.json earlier extraction has3gaps and17URLs because stalepage2 showedcentralduplicate; fresh18card listing includesKropaninka5721, readererrors. New exporter etl/normative_library_directory.py outputs datasets/normative/regional-libraries.json (12public+1child, no coords); literaldate2026-11-12 preserved as observed_at, generated_at buildonly. Sourcefieldsha describes extractedfields, notrawHTML. Duplicate/foreignURL/date/unreviewed rejectionbeforeoutput. Academic292noaddress excluded. Existing2GISchildren now children_library, outsideN07; regional/institutional profiles separate. N07now34addresses22coordinates12missing; totalcatalog810. Civicclassifier preserves distinction forregeneration. Ketovo officialKosmonavtov43, earliernoteLenina92corrected; localOSMway72357982saysKrasina41, no automaticcoordinate transfer.82OSMlibrarycandidates in.local/library-directory/osm-library-candidates.json, notimported wholesale.

N07newrealPOSTsaved+exactGETfromCompose8003 verified; latest artifact .local/normative-v4-N07-library-directory.json.1235origins/1234car times, allunknown. Separatingchildtargets changed0originstime/assignment vsprior24targetmodel; negativeevidence.local/library-directory-impact.json.13ETLtests+Ruffnewfiles, libraryintegration1passed/4deselected; backend345unitpreviousgreen unchangeddomain. Frontend440tests/36rules/types/Biome/build; Composefrontend rebuilt. Desktop1440/1920ComposeN07 searchKetovo, expandpubliccard, correctaddress+missingcoords, childrenabsent;JS/axe0/overflowfalse. Initialscripts guessedwrongsearchlabel then forgotexpandcard beforeassert; correctedpassed. Artifacts.local/library-directory-desktop-check.json, /tmp/normative-library-directory-{1440,1920}.png.

No commit/push, originalworktree untouched. Dev8082/8002 andCompose8083/8003 alive. Next: inspect agentcompletedresearchandextractreviewedaddress/profiles across full481publicationindex, deduplicate withsources, matchcoordinates byverifiedaddresses; no geographical/legalcompletenessclaim. Unanswereddepartmentaldataquestion stillpending. Fullgoalactive; don't repeatgreencheckswithoutchanges. Newestsourcefielddates maynewrunID; inspectactualJSON.

Finalcross-check: index26categories/66pages/481records, uniqueactualURLs481, categoryrecordcounts exactly matchpublishedmonthtotals; all14reviewedrecords/4unreadURLs aremembers. LatestN07date-preservingrun62cacc28d3cb4aa5a2644db94ff06cd8exactlyrestoredfromCompose8003. All code/dataevidence inspected; fullplanstillnotcomplete.


## Regional catalogue full checkpoint

Previousgoalturn=progress, thisgoalturn=progress. Separateworktree docs/normative-indices-plan@0c7cb89 no commits/push. Dev8082/API8002 running new source (exec73057), isolatedCompose8083/8003 images rebuilt, owncachevolume existingCH. No mobile/paid/provider calls. Current frozenN07 run5760601acfc24113a47cd12334ab879d in.local/normative-v4-N07-regional.json; exactrestore8002/8003. docs/results/normative-library-regional-validation.json records1235origins1234paths429facilities35coordinate_records407published_dates, alllegalunknown. On1234pairs vsold22coordinate model,986lower/0higher physicaltimes, unweightedmean129.230897→78.288634minutes. Route37502000101toyugov-library-589 has100networknodesandmatchesminutes.

All481primarybody attempts/read,26categories66pages. Source partitions work/research/library-addresses-{000-159,160-319,320-480}.json and.md:158+156+160addresses=474,4ambiguous,3missing,0unavailable. All481URLs/clean names/ISOdates/publishedclosureexclusionschecked. DirectwebopenURLerrors recovered via ACTUALCLICKchain root134→category→pagination→exacttitlecard; do not recrawl all. Errorseparator may lack leadingnewline; generic split prevents mismatchedbodies. SharedheaderKomsolskaya30 excluded. Sourcefields datebasis466ownbody/15listing. Body6715 closed2010 reopened2021; no falsecurrentclosedflag. Explicitcurrentclosed8642/8075 excluded. Other/tourist/multitarget exclusions raw retained. Middleprofile4150/4147/4146 correctedfromoperator-basedother tolibrary; source4913bodylibrarydespitenonlibrarytitle honored. Sourceinput datasets/normative-library-source-records.json completebodycoverage butNOTcomplete/currentserviceinventory.

Exporter validatesstatuses/profile/datesbeforeoutput; builds436facilityrecords(407public/28children/1academic),33duplicatealiases,12excluded. CivicGIS adds22public andotherprofiles; wholemodule1233records. Dedup conservativeprofile+ownidentity+address, legalprefix/yearnormalization, olderURLaliasespreserved; otherpotentialduplicatesremain explicitrecords, notclaimuniqueinstitutioncount. etl/normative_library_{directory,deduplication,matching,coordinates}.py are ownedentry/helpers. CoordinatesCLIuseslocalPBFamenitylibrary andpostcode+locality+streetkind+house exactmatch, onecandidateonly; clearspriorcoordinatesbeforematching.17coordinate_recordsallprofiles,13public+4child,1OSMnode+16buildingrecords, no verifiedentrances. Cataloguehashes referextractedfields; PBFhash/ODbL/matchingtags retained. Neveruseinstitutionnamealone toresolveconflictingaddresses.

Facility.published_on added nullable tocore/controller/OpenAPI/TS/Arrow/SQLcurrent+frozen tables. Reposselectnewfield; oldrunshavenull, nevercurrentcatalogdate. UI showsdatecardseparatefromread-date. Source.observed_atdate-only2026-11-12 stable, generated_atbuildonly. New normativepointsearch byname/ID includeswalkingaddresses; samecriterionkeyresetonservicechange alreadyimplementedinMapPage. Searchdoesnotchangecoverage/mapdenominator. Stageinitmanualtest couldn'tfindAlmenevo onfirstalphapage becauseplaceprefix; thispromptedrealUXsearchimprovement.

Ruff/mypy232files/345unitpassed;19ETLpassed; frontend442tests/36rules/types/Biome/buildpassed. Moduleintegration first4pass/1fail readingfullnationalnodes; system.query_log Code241 total2.33GiB memory, concurrentbackgroundsystem.metric_logmergesfailedtoo. Sharedserver/config notchanged. Libraryintegration repeated1pass/4deselected, exact429facilities+publicationdates restored. No fabricatedsingleall-green5/5claim. Frontformatter initiallyfailedoneTSXline, fixed. APItypes regenerated, Composebuild passed. Desktop1440/1920N07 sourcecard+newroute viaIDsearch JS/axe0/overflowfalse,sourcecarddate scrolledvisible; .local/library-regional-desktop-check.json and /tmp/normative-regional-library-{source,route}-{1440,1920}.png. N04search82117182real41236refsoneunknownrow/no0metres,0JS/axe/overflow; .local/normative-search-walking-desktop.json.

Fullplanincomplete: operationalcurrentness/verifiedentrances/adult&childpopulation/catchments/firevehicleprofile and legaleditions/territorycrosswalk. Nextconcretepublicdatastep: inspectofficialFNSOKTMO2024four-okrugdownload candidate, exactIDmatchingonly, preserve2024currentnessunconfirmed; work/research/municipal-crosswalk-candidates.md and normative-municipal-readiness.md. Do not askagainaboutdepartmentaldata, noanswerarrived. Goalactive. Don'trepeatgreencheckswithoutnewchange; do notrefetch481alreadyreadcards. No mainworktreeedits.


## Municipal encoding checkpoint

Previousgoalturnprogress, currentprogress. Ownbackgroundresearchworktree casechamp-crosswalk-research branch docs/municipal-crosswalk-research; researchoutputcopiedto parentwork/research/municipal-official-code-chain.md. No commits/push/mainworktreeedits. Dev8082/API8002 restartedexec15487(PIDlookupport); Compose8083/8003 rebuilt; readonly/publicwebresearch/no paid/mobile.

OfficialFNS2024DOCX/tmp/crosswalk-fns-oktmo-2024.docx copied.local/municipal-crosswalk/OKTMO-full-2024.docx:15467Bsha03051ab2fcd571969461311e39b151783c3c783457f0f0862de784f82abddd13. Sourcehttps://www.nalog.gov.ru/html/sites/www.rn45.nalog.ru/OKTMO.docx linkedarchived25Apr2024article14849279.26rows24MO/2GO. 2016officialFNSrn27article6061590explicit11→8budgetmunicipalcodehierarchy. 199H[:8]==McheckedindependentFNS4okrugXLSX(actual.local/municipal-crosswalk/OKTMO2024.xlsx35142Bhashe2cd..., structure-check.json). 0exactoldNPjoinsstilltrue, namematchesnotcertified. Gost610/2023publicmetadatasays37pagesbutimageswereauthorizationplaceholders; textNOTread/authnotbypassed. RegionalRosstatfolder33052/currentclassificationrecodingtablesnewleads, nofileyet. PotentialpublicGARregionalhistoryexportnext, notyetavailable.

etl/normative_municipal_codes.py pinshash/parses26parents, readsactualgraphpointIDs, matchesONLYEXACT8digitparentkey.382new375prefixparentsconditional;851old376noassignment.2manualcitycontextsnotclobbered(overridepriorityevenifcategoryconflict). datasets/normative-municipal-code-reference.json freezesreference2024/structure2016/currentnessfalse/assignmentfalse; normative-territories.json384contexts. NooriginIDrewrites/noOSM/nameassignment. MainimportvalidatesTerritoryContextandduplicatesbeforestorage; encodedmismatchrejected. WalkingarraywrongtypeinternalCLIbecameTypeErrortoalignTRY004, errorcopyunchanged, negativecasesupdated.23ETLtests.

DomainTerritoryContext optionalmunicipality_code+structure_source_url; ENCODED_PARENT_STATUSvalidatespoint11digits/prefixequality/source. AccessRow/HTTP/TS/Arrow/SQLcurrent+saved fields territory_verification_status,municipality_code,territory_structure_source_url. Reposelectthemforlatestandroutecontext, oldnullsnotreinterpreted. UIpointshows8codeandexplicit2024conditionalnotice, link2024codebook+2016structure; old376noexplanationandnullthreshold. Existingtwo40thresholds+382conditional60=384, ALL1235statesunknownandterritory_conditions_missingforcoded. Physicaltimesanddestinationssameasregionalrun576... . APItypesregenerated.

ActualComposePOST/GETdevexact: run42f886c0d9a4498bbf0ed4f418eba55c, saved_atinproofJSON. Artifact.local/normative-v4-N07-municipal-codes.json; docs/results/normative-municipal-encoding-validation.json. Historicalrun5760601acfc24113a47cd12334ab879dscenario1235rows2thresholds0codesverifiedinDB; initialassertmistookUInt64JSONstringsforints,fixedbyintconversionnoproductchange.

347backendunit/Ruff/mypy232files;23ETL;443frontend69files/36rules/types/Biome/buildpassed. Libraryintegration1passed/4deselected60s:384thresholds, exactsources/code/statusandrowsroundtrip. No needrepeatgreenchecks. DesktopcodedAlmenevo37502000101andlegacyBarashkovo37606151111each1440/1920:JS/axe0/overflowfalse, routesrestored, scopesexplicit. .local/municipal-codes-desktop-check.json and/tmp/normative-{encoded,unmapped}-municipality-{1440,1920}.png. No mainchanged.

NEWcompletionaudit finding: scope.py medical/fire.py/territory.pylibrary ALWAYSsetstateunknown; lacksverified-evidenceingestion/qualificationhooks analogouswalkingfacts. HonestforcurrentdataBUTcan'tclaimonlyexternalgatesremain. NextCODEpriority: N07typedverifiedconditions pipeline/qualification whileemptyactualregistryremainsunknown; thenmedicaladult/catchmentandfireoperationalfacts. Do NOTseedtestattestationsinproduction. Externaldataquestionstillunanswered,dontaskagain. Fullgoalactive/incomplete. 851old-IDcrosswalkandlegalcurrentness/publicserviceinputsremaining. Userinstructionfullplanunchanged.

## Library qualification checkpoint

Progress turn: N07 typed verified qualification added, no invented production evidence. Files: domain/normative/library/{facts,qualification}.py; usecase/normative/library_evaluation.py; ClickHouse library_schema.py; normative queries/repository/schema/store/SQL/import and UI source/point translations. Model v5; v3/v4 route replay retained. Frozen decision clock, source/date/raw input snapshots. 411unit/28ETL/443frontend and3 selected integration tests passed. Mypy243/Ruff pass; changed formatchecks pass, fullformat has pre-existing test_chat.py violation. Isolated CH test table dropped, current facts remains0. Compose updated8083/API8003; dev8082/API8002 restarted session82205. Actual N07runfdc3282426eb41ae938a36de83d93098 exact POST/GET, physically equals old42f886c0d9a4498bbf0ed4f418eba55c, allunknown. Evidence docs/results/normative-library-qualification-validation.json. Early desktop probes timed out due incorrect collapsed-section/button selectors, then AxeBuilder required explicit newContext; corrected repeat follows. No source bug inferred from those harness errors. Next medical/fire typed qualification, then remaining external gates. No commit/push; original tree untouched. Goal active, meaningful progress, blocked threshold not reached.

Desktop repeat1440/1920 passed:0JS/axe/overflow, real N07point search and source disclosure, no qualification timestamp for empty production registry. `.local/library-qualification-desktop-check.json`, screenshots `/tmp/normative-v5-library-{1440,1920}.png`.

## Medical qualification checkpoint

Previous turn progress (library v5); this turn progress (medical v6). `TransportFacts` extracts common typed transport validation, `LibraryFacts` inherits and retains municipality fields. New MedicalFacts/facts registry/qualifier/target evaluator; no production attestations. Care forms, ownership scope, adult cohort, catchment, regional adjustment source and explicit threshold are separate gates. Raw targets selected before routing; full inventory needed for negative conclusions. Source/date/decision clock/raw facts frozen. AccessRow/API/Arrow/SQL add catchment_source_url and threshold_source_url; UI shows selected threshold and separate sources, federal baseline labelled. v3/v4/v5 routes replay, actual v5 100-node replay verified. Model v6.

468 unit/Ruff/mypy256, 33 ETL, 444 frontend/36 rules/type/lint/build pass. 2 isolated CH evidence tests pass; medical real-graph integration1pass/5deselected22.4s after fixing missing graph_dir in harness. Duplicate pytest basenames fixed by package __init__.py. Startup-race type generation failed, authoritative startup confirmed then repeated successfully. All changed-format69 pass; pre-existing full-format test_chat.py issue retained.

Compose8083/API8003 rebuilt, dev8082/API8002 session21333 PID67166 (confirm before killing). N01runef405395cdad446ba8c8e5e1a0e3fb66, N02rund8caad8f81584c84950f668313d8c4d5, N07runfcfe7d1417f94524b3eb8adbeee73512, all1235unknown; medical P null; qualification_as_of null. ExactPOST/GET; times/targets unchanged from previous v3/v5. Files .local/normative-v6-N01/N02/N07.json, docs/results/normative-medical-qualification-validation.json. Desktop N01-1440/N02-1920 JS/axe0/nooverflow, map-ready canvas/legend screenshot viewed /tmp/normative-v6-medical-map-ready-1440.png. Fast first screenshot was loading, corrected explicit map-ready wait.

Real GET devN07latest503: system.query_log Code241 total2.33GiB while formatting, query12.2MB,06:14:16UTC. Repeat succeeded. Official current format docs/system.settings checked; no speculative setting change and no shared server mutation. This resource limitation remains. Next: fire verified qualification using explicit speed/direction/access/readiness/profile binding; queries.py249lines will need responsibility split. External legal/currentness/entrances/cohorts/operational data still missing, question unanswered, do not repeat. Goal active, no blocked threshold (meaningful code progress). No commit/push, original tree untouched.

## Fire qualification checkpoint

Previous goal turn progress medicalv6; this turn progress firev7. FireFacts inherits TransportFacts with emergency_response-only mode via ClassVar; strict bool/number/URL/period/object-population scope. Legal source+edition and method currentness+edition, exact speed AND profile assumption, adverse conditions, access/direction/readiness/object/reference/graph/closures separate. Fire exit statuses distinct, full inventory + all attachments required for negative conclusions. Chosen call location type10/20 before routing. Population only measured_objects cohort. Method only depot_to_object_travel; no dispatch/turnout invented. New sources travel_profile_source_url, measurement_method_source_url in AccessRow/HTTP/Arrow/SQL/UI. Actual production facts remain0.

TransportConditions extracts shared loading/decision clock/evaluation/qualification; queries158lines, newmodule151. Field snapshots savedlast metadata as before. Fire facts SQL in infra/clickhouse/normative-fire.sql, importer applies it after normative.sql; run_fire_facts explicit Arrow. v7, v3/v4/v5/v6 route compatibility. FireProfile rejectsbool domain; HTTP speed strictTrue also rejects bool/string, accepts JSONint. Firepoint gets own call threshold/source component; old parent library=true forfire fixed to service library only. Genericfire explanation now describes gates rather than falsely assuming every future evidence is missing.

530unit/Ruff/mypy267, 38ETL,445frontend/71files/36rules/types/lint/build pass.4selected integration/5deselected31.66s:3evidence temp tables roundtrip/drop and realfire profile+trace; productionregistries0. Changedformat82 pass; old fullformat test_chat.py baseline remains. One commandwrongcwd did not find files, corrected backendcwd pass; no code mutation by mistaken paths.

Dev8082/API8002 session23783 PID82861, Compose8083/API8003 rebuilt. RealN03run137ac70c89d44d3a991445824f22bd34,1235origins/1234times/9depots, allunknown, exactPOST/GET, qualification_as_ofnull, physicaltimes/targets/thresholds equaloldv3 sameexplicit40km/h. TraceKurgan37701000001 14nodes, depot→call approaches verified. .local/normative-v7-N03.json; docs/results/normative-fire-qualification-validation.json. Desktop1440/1920 JS/axe0/nooverflow, mapcanvas/control ready, realKurganrow selected,10minute call threshold+source no duplicate library municipality block. .local/fire-qualification-desktop-check.json, /tmp/normative-v7-fire-{1440,1920}.png viewed.

NEXT concrete phase3 gap: datasets/normative/fire.json ONLY9coordinate candidates; work/research/fire-response-readiness.md has26officialaddressrows (25withhouse), pages7–10 contactPDF source. Needfulladdresscatalog26with17nullcoords, preserve9exactcandidatecoords, name1/11conflict andstreetkind17no guess. PrimaryPDF mayneedrefetch/hash to .local/research before extraction; sourceURL in currentfire.json. Do not claim onlyexternalgates remain before this available data work. Then fullsixstageaudit. ResourceCode241sharedCH documented previous turn remains, no server configchanges. Question about verified inputs stillunanswered, donotrepeat. No commit/push/originaltreechanges. Goal active, meaningfulprogress, no blockedthreshold.


## Superseded completion audit before full fire catalog

# Проверка полного нормативного плана, 12.11.2026

Проверено против шести исходных этапов `work/territorial-indices-plan.md`, текущих требований `work/normative-implementation.md` и размещения всех услуг в исходном списке карты. Вердикт: **полная готовность не доказана**. Физическая модель и неизвестный правовой статус не заменяют условия приёмки исходного плана.

## Требования и доказательства

| Требование | Текущее доказательство | Вердикт и остаток |
|---|---|---|
| Отдельный worktree, исходная карта | `docs/normative-indices-plan`, HEAD0c7cb89; `MapExplorer`, `MapPage`, `/normative` перенаправляется на карту; фактические UI8082/API8002 | Реализовано. Коммитов/push нет |
| Этап1: реестр норм N01–N09, редакции, переходы, исключения, адресат | `datasets/normative/criteria.json`, исследования медицинских/пешеходных/пожарных/муниципальных правил;134страницы1169и56страницСПсохранены | Частично. Первичные тексты получены, но исчерпывающая актуальность ряда редакций не подтверждена |
| Этап2: подтверждённый пилот, профиль, применимость, целевая группа | Два подтверждённых взрослых кардиологических профиля;16координат МФЦ после адресного аудита | Не завершено. Здания не являются подтверждёнными входами, взрослых по пунктам и прикрепления нет |
| Этап3: входы, действующий статус, транспортные условия, версии/пропуски | `datasets/normative-sources.json`, локальные manifest/SHA,797записей объектов/профилей, pedestrian-v2 | Частично. Нет полного актуального реестра, проверенных входов/выездов, календарей, контингента и оперативных данных |
| Этап4: допустимые цели, время/метры, охват, превышения, отдельно мощность | Автомобильная, пешеходная и явная пожарная сценарная ветки; местные библиотеки отделены от4областных и1ведомственной; `coverage` сохраняет неизвестные | Частично. N04/N09 выбирают условный порог/применимость по типизированным подтверждениям; допустимые цели фильтруются до маршрутизации. Реестр подтверждений пока пуст. Обеспеченность мощностью не смешивается с доступностью |
| Этап5: закрытие/восстановление, альтернативный путь, изменение охвата/времени | Реальные закрытия way, исходная/сценарная геометрия, `comparison`, тесты параллельных альтернатив, потерянные пути отдельно; отсутствующие walking-way сообщаются | Техническая ветка реализована. Число жителей за юридическим порогом неизвестно без входов и применимости |
| Этап6: контрольные пути, исключения и юрисдикция, связь акта с расчётом |64пешеходных контрольных точки,49путей; unitусловиягород/село иГО/МО, профиль/стоимость маршрута; источники/версии сохранены | Частично. Полевая проверка отсутствует; школьные/зональные исключения ещё требуют кодовой ветки и исходных данных |
| Снимок, восстановление, воспроизводимая геометрия, даты | Типизированные Arrowснимки, модель/граф/присоединение/профиль, сверка стоимости, сохранённый `saved_at` сUTC; APIPOST/GETдата совпадает | Реализовано для текущих моделей. Старые unversionedпути требуют пересчёта; недоступная автомобильная версия выдаёт явную ошибку |
| UI/UX, ошибки, неизвестность, клавиатура, desktop | Исходный groupedSelect14опций, таблица50строк и поиск учреждений, источник сохранённого акта;1440/1920проверки безJS/axeошибок | Текущие сценарии проверены. Мобильные/платные проверки не запускались по инструкции пользователя |
| Запуск/проверки проекта | Отдельные devпроцессы8082/8002, реальный ClickHouse, frontendverify, backendunit и moduleintegration | Локальный запуск и изолированныйCompose8083/8003 проверены с существующимClickHouse. Восстановление всех данных с нуля не повторялось |

## Срез реального хранилища

Измерение `docs/results/normative-readiness-2026-11-12.json`, дата2026-11-12T02:18:25.420899+00:00. Это чтение текущего хранилища, не готовность правового заключения.

| Показатель | Точек | Найденных минут | Найденных метров | Статусовunknown | Условных порогов | Целей в снимке |
|---|---:|---:|---:|---:|---:|---:|
| N01 | 1235 | 1234 | 0 | 1235 | 0 | 2 |
| N02 | 1235 | 1234 | 0 | 1235 | 0 | 2 |
| N03 | 1235 | 1234 | 0 | 1235 | 2 | 9 |
| N04 | 41236 | 0 | 27577 | 41236 | 0 | 34 |
| N05 | 1235 | 1234 | 0 | 485 | 0 | 38 |
| N06 | 1235 | 1234 | 0 | 468 | 0 | 24 |
| N07 | 1235 | 1234 | 0 | 1235 | 2 | 24 |
| N08 | 1235 | 1234 | 0 | 1103 | 0 | 1 |
| N09 | 41236 | 0 | 27502 | 41236 | 0 | 658 |

N09в срезе — сохранённый сценарий закрытия8участков плюс1отсутствующий way, поэтому27502метровых пути не являются исходным числом27578. N04исходный pedestrian-v2имеет27577путей. Исторический школьный27578относился к352ce6...; текущий60dea...теряет ровноosm-way-82117182(РихардаЗорге15)после изменения правил сети. Сопоставленные текущие школьные снимки согласуются. Это не случайная нестабильность алгоритма.

## Следующие обязательные действия

1. Кодовая ветка и хранение условий N04/N09 реализованы: шесть школьных и две остановочные проверки, отсутствие универсального500м, раздельные нерегулируемые случаи, версия измерения и подтверждение сценария. Импортировать реальные подтверждения.
2. Подтвердить и импортировать входы/выезды, целевые группы/прикрепление, муниципальные/зональные условия и действующее обслуживание/подвоз; неподтверждённое сохранять неизвестным.
3. Завершить проверку правовых редакций и применимости; не приравнивать единичную позднюю ссылку к исчерпывающей истории изменений.
4. Повторить сценарные/юрисдикционные проверки на подтверждённых входных данных, повторить контрольные пути на местности. ИзолированныйCompose8083/8003 проверен.

Вопрос о наличии ведомственных данных отправлен команде, ответа пока нет. Кодовые условия и проверки реализованы; пустые подтверждения не заменяются тестовыми данными. Цель остаётся активной.


## Проверка условных правил v4

Ruff, mypy (232файла),345backend unit,5интеграционных тестов модуля,8ETLтестов прошли. Frontend:36правил,440тестов, типы, Biome и productionbuild прошли. Интеграционная проверка восстанавливает все41236строк и группы условий без изменений. ETLкоманда с одним `PYTHONPATH=backend/src` не собрала тесты из-за импорта модулейetl; исправленный запуск `PYTHONPATH=etl:backend/src backend/.venv/bin/python -m pytest etl/tests -q` прошёл.

Фактические базовые снимки v4: N04`168cc269678a473cb4d1223fa809b01d` —27577путей, N09`f7f431f6f9e94feb89daa4048fc89906` —27578. По41236точек; по одной нормализованной группе с6/2проверками. Все правовые результатыunknown, поскольку подтверждённых WalkingFacts нет. Предыдущие физические результаты не превращены в подтверждённый правовой охват.


Compose: текущиеобразысобраны, APIhealth/UI200, каталог9услуг, POST/GETN09v4совпали,41236строк/27578путей. Desktop1440N04и1920N09:0JS/axeошибок,0переполнений, геометрия1844/1767узлов. Источникподтверждения `.local/compose-normative-result.json`, `.local/conditional-desktop-check.json`; полныйпротоколвжурналереализации. Начальноезамечаниеaxeоcontrastво времяDisclosureанимации не воспроизводитсяпослееёзавершения. Эти проверки не подтверждают отсутствующие входные данные.


## Областные библиотечные публикации и текущая проверка

481/481телокарточекпрочитанычерезпервичныессылки26разделов/66страниц.474адресныхполя,4неоднозначныхстраницы,3безадреса. Вышедшийнабор436записейучитывает12исключенийи33проверенныхсвязиповторов; историческиеURL/датысохранены.2явнонедействующиебиблиотекиисключены. N07теперь429адресныхзаписей/35координатвместо34/22; это неутверждённыйполныйреестрработающихбиблиотек. Провереныиндекс+местность+видулицы+домOSM, непроверенныекоординатынеизобретались.

`docs/results/normative-library-regional-validation.json`фиксируетrun5760601acfc24113a47cd12334ab879d:1235пунктов,1234сопоставимыхвремени,986улучшений/0ухудшений, всеюридическиестатусыunknown.100узловконтрольногомаршрутадооднойновойцели,стоимостьсовпала. Nullablepublished_onзамораживаетсяиотделёнвUIотдатычтения. Добавленпоискпункта/адреса/IDдлябольшихтаблиц.

345backendunit/Ruff/mypyи19ETLпрошли. Moduleintegrationдал4passed/1failed(Code241общеголимитапамятиClickHouseнаузлах); библиотечныйтестпослесниженияресурснойнагрузкипрошёлотдельно1passed. Общийсервериполитикапамятинеизменялись. Frontend442теста/36правил/типы/Biome/buildпрошли. Полнотаисходныхпубликацийулучшилаэтап3, но непокрываетведомственныйконтингент,прикрепление,актуальныйсервис,входы/выездыиправовыередакции. Полныйпланещёневыполнен.


## Кодовые муниципальные кандидаты и оставшийся квалификационный код

ЧтениепервичныхФНСисточниковдало26кодов2024иправило11→8;199независимыхXLSXстрокподтвердилиструктуру. По входномуID382пунктаполучилиусловныйродительскийкод/60минсverification_status=encoded_parent_2024_assignment_unconfirmed,851старый376…неперекодирован,2ручныхгородскихоснованиясохранены. Географическаяпринадлежность/актуальностьнеподтверждена; allunknown. Run42f886c0d9a4498bbf0ed4f418eba55cсохранёнивосстановлёнточно; физическиевремена/целинеизменились; прежнийснимокосталсяс2порогами.

347unit/23ETL/443frontendи1библиотечнаяинтеграцияпрошли;4desktopкейса1440/1920(coded/legacy)безJS/axe/overflow. Источник `docs/results/normative-municipal-encoding-validation.json`.

Содержательныйостатокэтапа4: медицинская, пожарнаяибиблиотечнаяветкипокабезусловноunknownвscope.py/fire.py/territory.py. Однихбудущихведомственныхданныхнедостаточнобезкодовогоимпорта/проверкиподтверждений; нужно реализовать квалификационный путь дляпроверенныхслучаев. Это не закрываетсянормативнымменюилиусловнымпорогом. Текущиевнешниепробелытакжесохраняются.

## Квалификация библиотек v5

N07 больше не имеет безусловного запрета положительной квалификации: отдельный типизированный реестр проверяет действительность, закон, юрисдикцию, происхождение измерений, допустимые цели, входы, контингент и сценарий. Положительные/отрицательные случаи проверены изолированными тестами. Производственный реестр пуст, поэтому реальный1235точечныйснимокостаётсяunknown. 411unit/28ETL/443frontend и3выбранныхинтеграции прошли, Composeпересобран. Подробности в конце журнала реализации и `docs/results/normative-library-qualification-validation.json`.

Медицинская и пожарная квалификация остаются кодовыми задачами. Все внешние пробелы сохраняются; полный план не закрыт.

## Медицинский путь v6

N01/N02 теперь принимают типизированные подтверждения с отдельными формами помощи, взрослым контингентом, прикреплением, формой собственности, региональным порогом и проверенными измерениями. Допустимые цели фильтруются до маршрутизации. Исходные данные и основания порога замораживаются. Условная квалификация больше не запрещена кодом, но рабочий реестр пуст и реальные результаты unknown. 468 backend unit, 33 ETL, 444 frontend и три выбранные интеграционные проверки прошли. Протокол `docs/results/normative-medical-qualification-validation.json`.

Остаются квалификация пожарной ветки, внешние подтверждения и устойчивость чтения при нехватке общей памяти ClickHouse. Один реальный GET/latest завершился Code 241, повтор прошёл; это ограничение сохранено, а не объявлено исправленным. Полная готовность не доказана.

## Пожарный путь v7

N03 принимает типизированные подтверждения скорости/описания профиля, методики и её редакции, неблагоприятных условий, проезда, направлений, готовности, выездов и объектов назначения. Тип места вызова выбирается до маршрутизации. Положительные случаи проверены только изолированными тестами, рабочий реестр пуст. Реальныйrun137ac70c89d44d3a991445824f22bd34 восстановлен точно,1235пунктов/1234времени/всеunknown, путь14узлов от депо к вызову.530unit/38ETL/445frontend/4выбранныеинтеграции прошли, desktop1440/1920 безJS/axe/overflow. Протокол `docs/results/normative-fire-qualification-validation.json`.

Не завершён адресный каталог МЧС:26исследованныхзаписей против9импортированныхкандидатов. Поэтому утверждать, что остались только внешние данные, пока нельзя. Следующий шаг — полный адресный импорт с явными пропусками координат и новый аудит этапов1–6. Внешние подтверждения и общая памятьClickHouse также остаются ограничениями.

## Fire directory and source-version checkpoint

Previous turn progress firequalification; currentturn progress catalog26/sourcehash/UI/audit. Research skill required backgroundagent fire_directory_primary in OWN worktree /Users/savelij/projects/casechamp-fire-research,branchdocs/fire-directory-research@0c7cb89. Only own MD/SESSION, protected quotes kept; no code/DB/commit/push. Parent copied primaryPDF+MD. PDF197248B/13pages/SHA c7710fe218bf522a93bb1af8c0653316ef5c77dea6776a9d55bb5587856ac3d4, actualpages7–11viewed,26headers6+8+6+6pages7–10. Publication/editiondateunknown (uploadpath/CreationDate2025-02-13 notsame); observedNov12dateprecisiononly. 34housemissing,11not1,15ULnotPR preserved,staffcontacts excluded.

New datasets/normative-fire-source-records.json and normative-fire-coordinate-candidates.json; new etl/normative_fire_directory.py validates reviewedcount/hash/bytes/pages/IDs/sourceobservation and exactaddresses, prohibits exitpromotion; all26records kept,9exactoldcoords/OSMlinks preserved,17null, overall1250facilityrecords. Source manifest adds primaryPDF metadata. Candidate dates converted from imprecise00:00placeholder to known day. Current fire.json no longer falsely labels upload date an edition.

Facility adds optional source_sha256 (domainstrict64lowerhex, API, Arrow, SQL current+runfacilities, rowqueriesrestore/routecontext); CLI validates Facility before DB open, negativeETLtest pinsordering. UI nested DocumentVersion shows frozenhash onlyifprovided. Source hash isaddressPDF NOT coordinatePBF. Oldrun137=9/0hash/0page, interim68a7519ef80647448c7bedb2637619ec=26/0/26 unchanged. Finalrun61737ee8f3d64ef5a1909f80f646fd99=26/26hash/9coords/17missing,1235origins/1234times allunknown, exactPOSTCompose/GETdev, times/targets/thresholds/population identicalold9source. .local/normative-v7-N03-directory-source-hash.json; docs/results/normative-fire-directory-validation.json.

534unit/Ruff/mypy269,51ETL,446frontend/36rules/types/lint/build pass. Newfireintegration1pass/5deselected29.19s. Changedformat7pass; unrelatedfullformat test_chat.py unchanged. Typecheck/build first failed because TestingLibrarygetByRole doesn'taccept Playwrightexact; fixed, thenfullverify+Composepass. Firstdesktopsearchlabelwrong, fixedfromdictionary. Globaloverflow/axeinitially0butmanualviewcaughtclippedhash! FirstCSSnormalwhite-space insufficientbecauseglobalp break-word mincontent503px. Final gridminmax0 andhashoverflow-wrapanywhere: actualhash317px/client317 insidecell, sourceFits true. Desktop1440/1920dev ANDCompose JS/axe0/nooverflow andcellbounds pass, primarypage9,missinghousekept,nopublicationdateguess. .local/fire-directory-desktop-check.mjs rerunsfromfrontend via node--input-type=module stdin; outputs .local/fire-directory-desktop-check.json. Screenshots /tmp/normative-fire-directory-{1440,1920}.png viewed final.

Dev8082/API8002 execsession25844 PID97612 (confirmbeforekill); Compose8083/API8003 latestsourcehash+CSS. Modelv7 unchanged(numericalalgorithmunchanged). Actualreadinessaggregate refreshed nine latestsnapshot versionsv3–v7 withoutretagging, DBregistriesall0,1250records. Audit rewritten current; oldauditcopied to thisjournal supersededsection. Productdoc staleN03unavailable statement removed; MFCcurrentN05run02cd32a1620e4bd297df7864ddf64e97 APIverifiedwithin684044 unknown92617 total776661 lower88.07497737107953 upper100,16coords andno closures; old89.1description replaced. docslinks andgitdiffcheck pass.

NEXT concrete audit gap: N03 currently origins=repository.origins(territory) from ORIGINAL plexus_graph.locations 1235settlementcenters. TransportConditions rejectsunknownIDs and Firequalifier bindscoords/node; verifiedactualobjectdestinations cannot beindependentlyloaded without touchingoriginalgraph. Need ownnormative object-origin registry/attachment path, truthful object labels/basis/population semantics, snapshots, tests with realadapter arbitraryobjects. Do NOT describe remainingworkas onlyexternaldata. Then source-version chain forotheravailable sources and controlled large-read/Code241 diagnosis; no sharedserver settingmutations. Actualprivategate inputs stillmissing andasyncteamquestionunanswered; donotrepeat. Goalactive, no-blockedstreak (meaningfulprogress). Originalworktree unchanged, no commits/push.


## Fire object acceptance checkpoint

Branch docs/normative-indices-plan@0c7cb89 unchanged, no commits/push. Previousgoalturnprogress: deployed currentv8Compose andverifiedlaunch. Thisturnprogress: N03objectimport/API/UIacceptance, baseline/scenarioresulttablefixed.563unit/Ruff/mypy277,56ETL,451frontend/36rules/TS/Biome/build,isolatedobjectsnapshotintegration1pass. InitialETLBasesmallfixture lackednewfields caughttypecheck; addedtypedcoveragefields. Objectresulttestinitiallymatchedtwo unknownlabels withsingularquery, correctedexpectedcard+tablecount2. FirstBiomeruncwdrootfailednestedconfig; retriedfrontendcwd andpassed, no configchanges. No productionfakeobjects/facts, GETregistry[], POSTemptyobject503 preserveslatestNPsnapshot. Desktop1440/1920 onactualCompose confirmsdisabledcalculationwithvalidspeed/description,savedbasisunchanged,0JS/axe/overflow; screenshot1440visuallyinspected. RebuiltComposeUIafterbaselinefix. Snapshotpositivepathonlyprivateclonedtables/testgraph; cleanupfinally. Updatedauditremovesobsoleteindependentobjectcodegap; nextsourceversions/Code241/externalverifiedpilot. Sourcehashandobjectfields documentedinmethod/API/designnotes. No paidcalls/mobilechecks.


## Six source versions and read-memory checkpoint

Previous goal turn made progress, no blocked streak. Branch docs/normative-indices-plan@0c7cb89, no commit/push. Stamped784records afterverified rawbytes/hash/size/date, manifestsforfivecivicsources, repeatedID/address/profile/source/officialgeometry extraction; MFCconstantURL andoldobserveddate preserved.810/1250currentprimaryhashes. Reimportcurrentnormativetablesonly, allfourfactsregistriesandobjectregistry0.436regionalreviewedlibraryfields/4medicalprofiles stillno rawprimaryhash. NewN05run33e61f72404144fc9a6efe935ee1d912 v8:38hashes/1235rows, rows/coverage/criterion/graph exactlyold, POST=GET. Readiness9snapshotsaggregatesrefreshed, oldsnapshotsunmodified.568unit/Ruff/mypy278,66ETL,3selectedintegrationpass; frontendunchangedlast451.

LargeN04/N09HTTPbefore2.540/2.170s. Controlled82472rowN09query baseline142760023bytes/139ms, one-thread8192block96435660bytes/271ms, exactsemanticSHA2aa3be6466e924911a346f8ea7a136ee0aaee1e23412949fe45fd4b07d1e73e3. No-server-sort96403125bytes/205ms negligibleextraeffect; notimplemented. SQL SETTINGS underreadonly1 failedCode164; movedrequestlimits toHTTPparams andverifiedgetSettingreadonly1/maxthreads1/block8192. No globalsettingchanges. Readerconstructorvalidatespositiveintegers; separateinstanceonlynormativerepo, atlas/graphreaderunchanged. InitialtestmockreturnedBytesIOwithoutheaders; replacedResponse(BytesIO)ownheaders, Ruffmutableclassdefaultfixedbeforefullpass.

APIComposeupdated. ActualquerylogN04/N09memory96605061/96435036bytes. WholeHTTP3.078s/18.925swithconcurrentnewN05calculation18.478s; isolatedidleN09repeat2.971s. FullN09HTTProwsmatchDBsemanticSHA. Singleobservationsnotthroughput/concurrencyproof, globalCode241unresolved. Do notclaimfasterentireAPI.

MFCdesktop1440/1920 primaryhash/sourcefits;0JS/axe/overflow,1440screenshotvisuallyinspected. Firstscriptpathcwdwrong, secondattemptstilloldselectorusedfacilityIDwhilefacilitysearchonlyname/address; correctednameandcompleted. Noappchangesneededforchecks. Productdocs/APIdecisionnotesupdated, source+memoryJSONproofsadded. Next remainingprimarybytes/legaleditions/verifiedpilot and graphloadmemoryaudit. No paidcalls/mobilechecks/commits/push.


## Complete reviewed medical table and order identity correction

Previous goalturnprogress, no blockedstreak. Branch docs/normative-indices-plan@0c7cb89 unchanged; no commit/push. Foundexisting.local/research/medical-routing-1169.pdf (legacyfilename),39737633bytes134pagesSHA df1f8198bc0230f40d45a8483b9a2060962cdad5293daddca3b15c71016de2c9 exactlymatchesearlierprofileevidence. Priorclaimmissingmedicalrawcachewaswrong. Visuallyreadfirstpage/10–14: handwritten1469not1169. Researchskillexplicitlyrequiresbackgroundagent; medical_source_currentness usedownworktreecasechamp-medical-source-review/docs/medical-source-review; finalsingleMDcopiedintoresearch. Officialcard/catalogconfirms1469, p3p5repeals194of19.02.2024,p5annualreviewbyApril1/proposalMarch1.8catalogpages76cardsnewestJune2026doesnotproveexhaustivecurrentness. Noexternalmessages.

Expandedfrom2tofullreviewed17addresses(table2endscontinuationp14).16haveexplicitbothemergency/urgentcardiology; planned-onlyShadrinskCRBexcluded. Zero cardiologybedcountnotusedasformfilterwhenlastcolumnexplicitlylistscare.32profileentriesvs4prior,+28modulecount1278/842primaryhashes.2originalgeometriescopiedwithsource/oldobservationintocandidateartifactandaddress-checked;14newcoordsnull. Rawaddress/form/catchment/adultaggregatefieldsstoredinreviewartifact, notconvertedtopopulationweights. Newrecordobserved12Novreviewdate,actdate16Oct2025notpublicationdate. sourceURLincludespage10–13,all32PDFhashes. ETLbuilderwithrawbyte/identity/count/page/forms/coordinatechecks,77ETLtests pass.

Reimportonlymoduletables,fourfactsregistriesandobjects0. RealN01fb858a37eda44ba3be152e4c39c90d6c/N02b5673d347d2b48d7945a276c6f559d2a v8:16targets/16hashes/2coords,1235rowsallunknown/popnull. Baseline+scenario IDs/minutes/target/pop/state/thresholdunchangedvsprior2coords;POST=GETexact. NewAPIintegration1pass,Ruff/mypy279. Initialintegrationfilewritewrongcwdprefixfailedbeforefilecreated;correctpathrepeatedandpassed. Noappcodechanged; previousfull568unit/451frontendremainlastfullchecks. BrowseractualCompose1440/1920newMБ1/sourcepage12/unknowncoords/hashfits/0JS/axe/overflow,1440visuallyinspected. RawPDFpages1/2/10/11/12/13/14visuallyread. Docs correctedcurrentnumber/counts andannotatedoldresearchscope, historicalsnapshotsunchanged. ReadinessN01/N02aggregatesupdated/proofJSONsaved. Next14medicalcoordinates/open-sourceexactaddresscandidates,436libraryprimarybytes,globalmemory/currentlegalapplicability/verifiedpilot. No paidcalls/mobilechecks.


## Five medical address geometry checkpoint

Previousgoalturnprogress, no blockedstreak. Worktreebranchdocs/normative-indices-plan@0c7cb89 unchanged,nocommit/push. ExtractedsavedPBFwithpyosmium4.3.2(ephemeraluv--withenvironment;backendruntimeunchanged). Backend/systemPythondidnothaveosmium, isolatedrunnerusedandlive15387polleduntilterminal; no timeoutrestart. Broadinitialstreet/houseprobe recordedmanywrongtownmatches; acceptedmatcherrequiresall3explicitcity/streettype+name/exacthouse+singletonclosedbuildingway. No city inferredfromname/county. Administrativeboundaryprobeexactnamesempty; relationsshowurban/districtmunicipalnames,notsettlementboundaries, sonotused. FiveacceptedLBway137285439,Ketovo72226801,Mishkino700868193,Shumikha581818883,Kataysk633646086. Makushino237887869+238097387sameaddress(includingbank)keptambiguous. Planned-onlyShadrinskCRBstillnotatarget. StreettypecanonicalКраснаяПлощадьmustretainулицаasindocument; correctedcanonicalparserandtested. Missingtype/locality/housevariantsfail.

Newbuild_medical_osm_candidates.py(42lines),normative_medical_matching.py(84),medicaldirectorybuilder114. Immutablepreserved2geometriescombinedwith5geocoded_buildingcandidates,PBFbyteshash8fb994e69910d29708416000cb718a9843a02576f5c45c1cc8e009fcb2d7f87c/ODbL1.0/extracttime11Nov00:02:04UTC/review12Novinartifact. Vertexmeanexcludesduplicatedlastvertex; no entrance/insidefootprintguaranteeforcomplexshape. ValidatemergeblocksPBFmismatch/orphan/duplicate/oldcoordinateoverride/wrongtags/statuspromotion.90ETLpass;realupdatedcatalogintegration1pass/Ruff/mypy279. Backendlogic/frontendcodeunchanged,lastfull568unit/451frontend.

Importedonlynormativetables,factsandobjectregistriesstill0,1278profiles/842addressPDFhashesunchanged.7coords/9missingperform. NewN01c20c49e2ab474c0c8aabadc87f394232/N0260e182f5def348208780f4867e78d861:1235rows/1234times,790reducedphysicalminima,noincreases,allunknown/popnull. POST=GETexact,route37502000101toMB7exact53.78043598229353min. Historicalrunsunchanged. UIactualCompose1440/1920candidatebuildingunverified/OSMlink/separatePDFpage12+hash0JS/axe/overflow;1440visuallyinspected. Docs/readinessupdated/coordinatevalidationJSON. Nextconcretecodegap:coordinatePBFhashstoredsourceartifact+datasetbutnotasindependentfrozenfacilityfield. Thenremaining9medicalcoordinates,436libraryrawbytes,2026legalapplicability/confirmedpilot/sharedmemoryCode241. Fullgoalactive/unproven. No paidcalls/mobilechecks/commits/push.


## Coordinate snapshot checkpoint and national scope correction

Current: docs/normative-indices-plan@0c7cb89; no commit/push. Coordinateprovenanceimplemented/deployed: Facility.coordinate_snapshot_sha256+url fromdomain/HTTP/Arrow/SQL toUIseparatedisclosure.786/790currentgeometryrecordsverified(GIS721,Nominatim34,PBF31),4officialmedicalprofilesunhashed.26OSMobjectsre-extracted;4firewaycoordsreproducearea_centroid,othersnode/vertexmean;roundingtolerance5.1e-8degree.575unit/Ruff/mypy280,93ETL,452frontend/36rules/fullverify,2integration pass. RealnewN01 5a34d23654084849957b4aa5181381a9/N02 f897ddcfff574eea85b016500cb2915f/N05 8338ba66a6bd4b95820ff2d351afb4be/N03 bc772fd28dc84ddaa9c6760f398647b1 freeze5/5/16/9coordinatehashes;rows/coverageunchangedPOST=GET;all4priorsnapshots0hashesunchanged. DesktopN01/N05x1440/1920bothhashesfit,0JS/axe/overflow. Proofdocs/results/normative-coordinate-snapshot-validation.json. Docs/readinessnotyetfullyupdatedforthischeckpoint.


AnsweredURL8083;usercorrectlyobjects pilotonly+graymap. PRIORITY NOW nationalregion/data integration and actualvisiblephysicalcosts, notmoremetadata-onlywork. Identifiedhardcodedcriterion.territoryKurganandcameraSelectionforcesnormativeRegion;allunknownstatusesgraydespite1234times. Mainplanhasnotnationalizedservices. Existinggraph84regions155747origins,atlas82;do notclaimsamecounts. ExistingnationalmedicalF0329980legaladdresses82regions,N033noactualaddresses;Ugraactualcareprofiles2121/1077addresses,Stavropol1165/926addressstrings. Rawfilesabsentonthismachine;notinCHmedicaltables. Agentnational_service_sourcesresearchskillrunninginownworktreecasechamp-national-source-review/docs/national-source-review;foundnationwidebusstations635totalbutdefaultendpointitems10(paginated!),stillcheckingpagination;F032zipreacquired1533841bytes. Do notimport10as635 orlegaladdressesasactualcarelocations. ProposednextUI: explicitregionselection/stopforcedKurgan, traveltimevslegalstatusviewdefaultphysicalcosts+visiblepathcounts. Backendneedsregion-scopedfacilities/criteria, unknownlocalrulescannotreuseKurgan178elsewhere. Goalactive,broadworkongoing. Originalrepo untouched;Compose8083/8003live,dev8082/8002oldAPI.



## Superseded runtime and scenario context

 Integrated settlement picker and effect table with national graph, not remote endpoint-only approximation. Real UI12min connection completed with1275affected origins/top30rows. Backend176tests and frontendverify pass. Amend requested for latest local commit; no force-push. Details: work/scenario-form-integration.md.

Branch feat/map-first-ui, HEAD 0c7cb89. Latest UI8080/API8000 and restored ClickHouse
are running; graph viewport and atlas HTTP checks pass. No commit/push. Runtime,
failed checks and limits: [record](../work/local-runtime-savelij-2026-11-11.md).
Protected instruction history exceeds SESSION budget and is preserved verbatim.

## National catalog and visible data checkpoint

Branch `docs/normative-indices-plan`, SHA `0c7cb89`; no commits/push. Worktree only `casechamp-normative-indices`. Compose8083/API8003 deployed after frontend fetch gating and catalog-only legend correction. Original8080 untouched.

New national API `/api/v1/normative/regions/{region_id}/catalog/{criterion_id}` reads separate ClickHouse inventory. Region selection no longer resets to Kurgan; foreign regions suppress pilot results, facilities, calculation action and pilot API fetches. Generic OSM medical points remain unconfirmed medical objects, not adult cardiology proof. Outside pilot no national assessment/routing yet. Physical times/distances default in pilot; legal status explicit alternative. A catalog with no assessment shows candidate legend only.

Acquired/extracted/imported6districts: central, far_eastern, north_caucasian, northwestern, siberian, southern. Latest exact DB206202unique OSM objects/68represented regions; border regions partial. Medical14919, schools20589, fire2814, libraries4417, stops137722, bus stations1474, MFC candidates1303, employment candidates159. Categories can overlap; objects are not unique institutions. Proof `docs/results/normative-national-inventory-validation.json`. Refresh with sourced `.env.analytics`, `PYTHONPATH=etl backend/.venv/bin/python etl/validate_national_inventory.py`.

LIVE acquisition handle36669, OS PID89685, script `etl/acquire_normative_national.py`. Southern import first failed with shared ClickHouse Code241; bounded single-thread imports/1000-row batches and memory-error retries succeeded. Now ural/volga downloading/queued. Do not restart based only on observation timeout. Sequential import watcher handle88536 runs `.local/import-national-pending.py`, waits for acquired manifest entries, extracts via pinned osmium4.3.2/Shapely2.1.2, imports, stops after2remaining districts. Do not start competing extraction/import. It captures existing `.env.analytics` and PYTHONPATH=etl; no secrets printed. Check same handles, actual PID/manifest. Once finished refresh proof and docs counts; no frontend rebuild required for new objects.

Verified current code:578backend unit/Ruff/mypy285;100ETL;458frontend tests/full verify. Real DB regional integration1pass (handle10133). Latest deployed desktop1440/1920 browser check passed (handle76689), output `.local/normative-national-browser-check.json`; earlier same check passed0JS/axe/overflow,1881Moscow medical/501Stavropol schools,1234/1235pilot paths, no pilot leakage. Screenshots `/tmp/normative-national-{regionId}-{width}.png`. Latest browser adds absent travel legend when no routes. Only desktop; no paid calls.

Source research complete in `work/research/national-normative-sources.md`; agent worktree preserves F032zip/Ugra actual-care XLSX. F032legal addresses cannot replace care locations. Full plan remains open: national routing, regional legal sources, facility eligibility/entrances and relevant population/service facts are not supplied by raw OSM catalog.

## Regional road measurements and complete map inventory

Branch docs/normative-indices-plan@0c7cb89; no commit/push; original worktree/8080 unchanged. Updated worktree Compose8083/API8003 healthy, latest source deployed. The user reported no visible change after11hours; acknowledged excessive time and incomplete full plan, gave direct Moscow URL. Do not claim full completion or spend the next turn only on provenance/tests.

All8districts plusCrimea/Sevastopol supplemental extracts acquired, hashed, extracted and imported. Final mapped inventory279736unique OSM objects/84existing map territories; zero territories without any object. Not all services in all territories and not verified completeness. Supplier source paths and spatial project boundaries retained independently. Full proof docs/results/normative-national-inventory-validation.json. Acquisition36669/9294 and import88536 are terminal; do not poll/restart them. Supplementary Sevastopol points mostly fall outside existing map boundaries; they remain in raw extraction, no forced assignment.

RegionalRoadMeasurements implemented in clean usecase/repository/controller modules, generated API/TS, table plexus_normative.regional_measurements. Car physical measurements forN01/N02/N05/N06/N07/N08 only; schools/stops/fire reject ordinary car substitution. Snapshots freeze facilities/hashes/geometry/rows, no legal thresholds. N01/N02 population null; all qualification unknown. Latest queries scoped to region+criterion. Real path endpoint checks saved cost. Moscow293/293 paths/1881generic medical candidates, not verified cardiology. Initialrun077b638d998949bc956abef229b3581b POST=GET. Scenario538960385:1path+2.1549962867min,292unchanged,0improved. Weighted multisource Dijkstra with virtual target offsets and latitude-index attachment. Closure modifies affected CSR pairs while preserving unclosed parallel edges. Exact before/after baseline+scenario rows. Timed one request each25.775341→2.075842s; no statistical benchmark claim. Proof normative-regional-road-validation.json.

UI uses shared PanelActions, typed regional queries, same table and point components. Regional times/ranges/map routes, baseline/scenario, reload restore. Copy says normative status unconfirmed rather than blanket missing data. Full frontend458tests/36rules/TS/Biome/build. Backend591unit/Ruff/mypy294;100ETL; selected real integration2pass (regional storage private-table snapshot+catalog). Latest desktop1440/1920 confirmation0JS/axe/overflow,293origins/74route vertices, stage switch/reload. .local/normative-regional-measurement-browser-check.json, /tmp/normative-regional-measurement-{width}.png. No further UI polishing loop needed without new defects.

A deployed API startup failed: graph nodes ArrowStream was truncated by CHCode241 (query_log confirmed). Changed only this app graph snapshot reader to bounded normative_reader (1thread/8192), caught HTTPException as DataUnavailable; test verifies truncation is explicit. Restart after code change healthy. Original atlas reader/server settings unchanged; global memory pressure not declared fixed.

LIVE batch: exec27648, OS PID62897, `python3 etl/calculate_regional_measurements.py`. Log .local/regional-measurements-batch.json. Last authoritative checkpoint56outcomes/49successful across10regions; remaining7are source gaps/other statuses, inspect log rather than assume. It calculates6car menu indicators across84map territories sequentially, writes real snapshots. No paid keys. Do not restart solely from timeout; inspect same process/handle. Resume flag assumes unchanged inventory/graph. No frontend rebuild needed as batch populates. Next verify full batch outcomes and persist evidence.

Full goal still active. Next actual scope: national walking networks with explicit region/network selection (existing walking repository picks global latest: importing another graph without fixing scope would breakKurgan), separate regional emergency/fire profiles, regional legal sources and verified operational/population/entrance facts. User's unanswered question on departmental inputs remains pending. National catalog/car measurements cannot replace these requirements.

## Indices priority and regional walking pipeline

Latest user instructions are preserved verbatim in SESSION: asks where indices are and explicitly prioritizes indices. P0 is now numerical indicators in the original map dropdown/panel with formula, denominator, source act and explicit uncertainty. Do not spend the next turn only on source expansion or polishing.

DEPLOYED8083/API8003: new GET `/api/v1/normative/regions/{region_id}/indices/{criterion_id}`, pure domain index calculation,9stored bases (4federal,5Kurgan regional), top-of-panel numeric card. Conditional known-object estimate is distinguished from legal compliance. No missing adult-population denominator is replaced by general population. BuryatiaN01:432/633points within60min,17paths missing,68.2464454976%; population percent null. UI68.2%, explicit point denominator, source132n and published-edition/currentness limits. Other regional acts are not inherited fromKurgan. MoscowN05 basis=null, no fake60min. Index proof docs/results/normative-index-validation.json, browser .local/normative-index-browser-check.json, screenshots /tmp/normative-index-{1440,1920}.png. Final browser waited for633map points;0JS/axe/overflow, card at top. Two visual rounds completed; avoid further cosmetic loops. Backend595unit/Ruff/mypy302;102ETL;458frontend/fullverify;2real index HTTP integrations pass. Main full goal remains unachieved.

Fixed regional road origins by own spatial registry:155659existing graph points uniquely intersect84project boundaries;88outside/noambiguous, no nearest fallback. Snapshotc5de885cd8c8f5f437fe342d, proof normative-regional-origin-validation.json. Repository reads byregion_id and matches current graph revision. Source atlas/graph tables untouched. NAO42/SPb1/HMAO194/Chukotka25. Old snapshot receipts unchanged. New API deployment uses this registry.

RegionalMeasurements (renamed fromRegionalRoadMeasurements) now selects car/walk/emergency_response. Regional walking factory/repository binds graphs byregion+purpose; existingKurgan versions explicitly registeredpurposepilot. Physical network publication cannot replace pilot. Optional fire_profile required forN03, no default speed, restored from snapshot. Frontend still exposes car calculation only; walking/fire control hookup and numerical completion remain pending. Regional walking uses spherical KDTree; pilot preserves prior projection/trace behavior.

LIVE raw walking extraction exec60740, childcentral_federal_district PID86340 at last inspection;9/10complete (all exceptcentral). Pipeline command uses pinnedosmium4.3.2/Shapely2.1.2/PyArrow26; sequential source processing. Raw extraction partitions roads and residential refs by actual project polygons, respects existing foot restrictions, barriers and foot directionality; dateline ways split spatially rather than crossingEurasia. Allraw inputs stored.local/normative-regional-walking/raw. No restart from timeout.

LIVE pending assembly/import exec57117, PID72909 confirmedwaiting. Waits for ALL10complete raw manifests, then runs assemble_regional_walking.py for84regions. Assemblies deduplicate shared nodes/edges/homes; conflicting geometry and incident edges excluded/counted; private derived revision paths. Networks publish only after exact DB counts; bindings purposephysical. Not yet any assembled/published regional network at last checkpoint. Newraw/assembly code and tests cover deduplication/conflict exclusion; metadata publication/storage path still needs real verification. Check free disk/RAM before large assembly;58GiB free before raw extraction. No independent competing extractor/importer.

CAR BATCH27648 terminated after382outcomes/336success/64regions: uncaught transient non200catalog GET. Actualhandleterminal confirmed; PID62897missing. Added bounded catalog retries and records failed catalog outcomes instead of aborting or calling them empty. Resumed with--resume at NEW exec7174, preserve old successes/log. Log .local/regional-measurements-batch.json; deduplicate by(region_id,criterion_id) when counting final coverage because resumed failed outcomes append. Originalbatch had old name-mismatch failures; resume uses fixed spatial repository. Do not restart solely from observation timeout.

Next P0: regional legal bases forN05/N06/N07/N08 and useful numerical indices acrossavailable regions; then connect walking/fire controls as their actual models/data become ready. No law-compliance claim from generic OSM or arbitrary national threshold. Existing legal-source132n/SP4283official URLs timed out in this turn; reused previously reviewed published sources with currentnessunconfirmed. SourceRNGP178page again states edition08.02.2023/registry24.04.2025.


## Country index overview

Default normative display is now numerical index, with all-region table, country choropleth and no forced pilot selection. Summary storage checks current run and legal-definition hashes; missing inputs stay null with a reason. Population and reference-point denominators are separate. Kostroma regional thresholds imported from official municipal publication; SPb transit/pedestrian thresholds retained in research and not applied to car measurements. Full frontend verify458 tests; backend597 unit tests, Ruff, mypy305 passed. Regional car batch finished504 outcomes:479 successes and25 empty candidate catalogs. Index publisher completed165 new summaries. Live verification follows Compose rebuild.

Country index overview implemented, pending final live check: map/table via /normative/indices/{criterion}/regions, no forced Kurgan selection. Full frontend verify458 tests and backend597 unit/Ruff/mypy305 passed. Regional car batch terminal:504 outcomes,479success/25empty catalogs, no failures. Publisher terminal:165 new summaries. Compose rebuild exec23465. Next: desktop country screen and Kostroma checks, publish direct URLs. Full legal coverage remains incomplete.

Verified country overview deployed8083/API8003. Live API: N01/N02 ready84/84 each; N05/N07/N08 ready2/84, N06 ready1/84. Missing regional bases remain explicit. Desktop1440/1920 country map/table and Kostroma81.4 checked, no forced region,0JSerrors/axeviolations/overflow. Screenshots /tmp/normative-index-map-{1440,1920}.png. Initial duplicate landmark fixed by distinct scroll label; full frontend verify458 rerun passed. Backend597, mypy305, Ruff and ETL102 passed. Browser proof .local/normative-index-map-browser-check.json, API proof docs/results/normative-index-map-validation.json. Compose rebuilds and batch/publisher terminal. Next priority: additional regional legal bases and matching transport models, not inventory expansion. No commit/push. Full goal incomplete.

Superseded checkpoint retained:
All10extracts imported:279736objects/84map territories. Physical regional car measurements implemented for6services; batch resumed exec7174 after catalog failure. Next: finish/verify batch; region-scoped pedestrian networks, emergency models and regional legal sources. No national compliance claim. Never use legal addresses as care locations or Kurgan thresholds outside Kurgan. Goal active;8083live.


## Expanded regional bases and national walking indices

Previous goal turn classified as progress: deployed country table/choropleth and verified84regional summaries for each medical branch. This turn adds19total bases (was13): SPb N05/N07 mode guards and explicit unregulated N08, Sverdlovsk N05/N07, Samara N08. Research skill background agent worked only in its own casechamp-national-source-review worktree; final primary-source record copied to work/research/regional-index-bases-next.md. Scoped Samara MFC/library absences, Sverdlovsk rural/group-specific bus thresholds and Tatarstan kilometre/worst-settlement rules are not imported into an unfiltered regional coverage.

SPb45/30min pedestrian-transit bases return model_unavailable without percentages. SPb bus station returns not_regulated without zero. Act currentness remains unconfirmed. Index API now carries weighting from the same domain rule used by the country map, preventing fire's known-population denominator from replacing its point denominator in the card. Corrected after live browser found missing9.5: card had preferred population indiscriminately. Indices remain conditional known-candidate estimates.

All84physical walking networks completed/imported, independently counted in ClickHouse:76089511nodes,161590339edges,6420158residential references. Started national N04/N09 batch, exec94521/PID15028, log .local/regional-walking-measurements-batch.log/JSON. Process was SIGSTOP only for compatible API deployments and SIGCONT after health; never leave stopped. Latest exact outcomes must be read from JSON, early503for PrimoryeN04/N09 and AltaiN04 remain for later retry. No invented legal status or population. Publisher watch exec98178/PID22750, log .local/regional-index-publication.log, confirmed live. Earlier publisher failed terminal on transient storage500; bounded unavailable handling added before restart.

Large walking writes exposed one-JSON-field memory failures in shared ClickHouse (Code241 allocating512MiB). New measurements use separate typed Arrow row/facility tables with explicit positions and counts, metadata published last. 8192row batches,1thread, parallel parsing disabled, bounded retries only on explicit memory-limit rejection. Existing snapshots stay readable, no historic rewrite. Schema infra/clickhouse/normative-regional-snapshots.sql applied; docs/running.md contains the exact command. Real private-table integration preserves10003rows per stage including reverse order/Float64 and rejects deliberately removed row. Backend602unit/Ruff/mypy307;3affected storage/API integrations passed;ETL102;frontend458/fullverify passed after UI changes.

Regional UI supports walking calculation and correct metre counts/table/point details. Fire scenario requires explicit speed and assumption; no silently chosen speed, regional origin reference is settlements. Saved fire assumptions are displayed. Index mode skips building invisible point geometry. Atlas air/rail transfer lines are hidden for normative metrics after desktop inspection showed unrelated flights on school map. Original economic metrics retain their overlays. Actual independent formula checks: docs/results/normative-expanded-indices-validation.json. NenetsN04=342/1322 at500m,707/1322 at800m,839/1322 at1000m. NenetsN03 explicitly assumed30km/h:4/42within10min,5/42within20min. SverdlovskMFC=3547357/4268998=83.0957756%;SamaraN08=3096299/3172925=97.5850044%. No adult-population compliance claim.

Latest Compose8083/API8003 healthy; final deployment log /tmp/normative-modes-final-deploy.log. Browser verification exec66907 completed:1440/1920,0JS/axe/overflow; Sverdlovsk83.1/source, SPb mode/unregulated guards,1322school points/metre note/calculation action and fire profile fields verified. Screenshots /tmp/normative-sverdlovsk-{1440,1920}.png and /tmp/normative-regional-school-{1440,1920}.png inspected. Proof copied to docs/results/normative-expanded-index-desktop-validation.json. First pass exposed denominator mismatch, fixed before final check. Next: finish desktop1440/1920 verification; retry failed walking outcomes after current live batch finishes; reduce heavy region-detail reads; extend regional primary bases and qualification inputs. Full plan remains incomplete; no commit/push; original worktree and8080 untouched.

Checkpoint walking outcomes40distinct:37success/3historical503. PID15028 batch and PID22750 publisher confirmed live and not stopped. All current deployments/checks terminal; full plan remains active. No paid/mobile checks. Next action: monitor same batch, retry its failed regions after terminal, optimize heavy index/detail reads and extend region-specific legal inputs.


## Cached index cards and compact batch receipts

Previous goal turn classified progress:19bases, matching-mode guards, national walking start, normalised snapshots and verified desktop. This turn fixed heavy per-card route reads. IndexSummary stores the full compact RegionalIndex. Repository validates latest measurement id, definition hash and complete basis equality before using it; absent/stale cache recomputes, never serves stale values. A real private-table integration proves equality, rejects a new run and changed law, then accepts the freshly published result. `index_payload` migration applied by publisher; main API wired to optional cache. Missing bases, unregulated cases and pedestrian-transit mode do not load full snapshots.

Frontend index mode now requests only compact index/map data; full catalog and measurement hooks are disabled until «Посмотреть пути и объекты». Kurgan's index view now uses the same regional snapshot as country map (N05=52.7), not the older pilot's88.1. Other views retain qualified pilot code. Desktop1440/1920:0catalog/measurement requests on opening,0JS/axe/overflow; physical paths action loads1322Nenets origins. Proof .local/normative-fast-index-desktop.json. Source rows and percentages unchanged. Single local observation each on same SverdlovskN04 run/145734references:44.307553s before,0.164439s after,2125response bytes both. Not a controlled benchmark. Proof docs/results/normative-index-latency-validation.json.

Walking process PID15028/exec94521 was confirmed terminal: uncaught IncompleteRead while receiving>1GiB full KrasnodarN04 response. Actual run af7636df4c3247a3a99d26af909968ac had already saved. SQL independently counted526926baseline+526926scenario rows;320465paths. Added GET/POST /normative/regions/{region}/measurements/{criterion}/receipt, compact typed result after real calculation/save. GET reads final metadata and comparison counters. POST/GET NenetsN05 exactly equal;625bytes,42references/25paths. Krasnodar receipt408bytes in0.0695s. Proof docs/results/normative-regional-receipt-validation.json. Full endpoints retained; large physical-view payload pagination remains open.

Batch updated to use receipts and reuse saved base runs on resume, with bounded transport failure handling. Restart justified by confirmed terminal exception, not observation timeout. Resumed exec9882/PID44221 after deployed receipt endpoint. First historical PrimoryeN04 storage failure repaired:221223origins/167318paths,25.676s,68ccc2a1350f4763b36009aab3146dc6. Latest distinct statuses must be read from JSON; historical failures remain recorded. Publisher old22750 terminated before compact-cache backfill; current exec71935/PID35666 confirmed live, transient unavailable inputs retried next pass. Never restart on an observation timeout.

Checks603backendunit/Ruff/mypy309;4affected integrations across cache/index/snapshot (cache+index3pass and snapshot1pass);102ETL;458frontend/fullverify. Compose8083/API8003 healthy, latest API-only deploy /tmp/normative-receipt-deploy.log. No commit/push or mobile/paid checks. Current source/status next actions: confirm receipt batch continues and repairs failed outcomes, reduce huge physical-view responses with paging, complete national walks, extend regional legal sources. Research-skill followups active in their own worktrees: national_service_sources prepares regional-index-bases-more.md (Voronezh/Belgorod/NAO primary scans); medical_source_currentness checks132n/495n chain in medical-index-basis-currentness.md. Do not claim those pending findings are imported. Full goal remains active and incomplete.

Checkpoint:55distinct walking outcomes, all55success. All3earlier503 repaired on resume; KrasnodarN04 reused saved receipt. Batch44221 and publisher35666 confirmed live. Desktop proof also copied to docs/results/normative-fast-index-desktop-validation.json. Full national completion remains unverified and open.

Final desktop pass exec41267 also waited for actual map readiness:1440/1920 all green, Kurgan1920 screenshot visually inspected after map loaded. API receipt deployment healthy, live POST/GET proof completed. No remaining local build/check process; only the intended national batch/publisher and research agents remain active.


## Dated medical review, local source intervals and national walking completion

Previous goal turn classified progress: compact index cache and receipt-based batch recovery. This turn adds typed IndexBasisReview (reviewed_at, as_of, locator, source URL/SHA/scope) and typed source intervals.21bases now imported. Medical60/120 unchanged. Source XLSX independently inspected with stdlib ZIP/XML:138582bytes, SHA7091246c7876b6c1a69807c7bc482cb9f5d1f5b0c4769ae54665f4cfda1d1c62, sheet1!A226:J226, position215,132n/41485 and Requirements2/3. Dated registry_listing22.10.2026, checked12.11.2026, does not assert complete currentness or OSM clinical eligibility. Primary webpage was also browsed and explicitly links edition22.10.2026. Full agent research copied to work/research/medical-index-basis-currentness.md;495n is infectious diseases, not a reapproval of60/120.

Regional source note copied to work/research/regional-index-bases-more.md. NAO/Voronezh N07 source intervals retained with municipality, mode and profile; regulation=local_selection_required, thresholds=(), no percentage until actual local selection/applicability is established. Ambiguous walking/transport alternatives remain explicit. Scoped historical Belgorod non-norming not expanded to entire contemporary region. UI source review and source intervals verified1440/1920:0JS/axe/overflow; medical68.2 unchanged, original Voronezh30–40/30–60 preserved. Artifact docs/results/normative-basis-review-desktop-validation.json, screenshots /tmp/normative-source-intervals-{1440,1920}.png inspected. Private-table integrations verify interval round-trip and no cross-region leak; cached nested review round-trips.

Walking batch PID44221/exec9882 completed:168distinct successes,171raw log records retaining3repaired historical503. No restart needed. Initial all-region receipt verifier failed terminal at Voronezh20000000/N04 after4HTTP503; ClickHouse query log proved241/512MiB ParallelFormattingOutput on legacy one-field JSON read, not missing data. RawBLOB read of the SAME saved run434eeef7d36d4033ae97845066f54547 returned120340origins/90654paths in5.41s locally. Regional repository now uses RawBLOB for payload reads, and legacy receipt extracts array sizes/counters without materialising row DTOs. Immutable snapshots not rewritten. Real private-table integration covers old JSON with absent mode/unit fields and new Arrow snapshots. Live Voronezh receipt after fix120340/90654,8.31s under parallel verification load.

API redeploy first exited1 on graph-edge loading/DataUnavailable (confirmed terminal). Retried stopped service once; healthy after39s. This was not an observation-timeout restart. New API/UI8083/8003 healthy. Publisher former56156 terminated and replaced exec65303/PID66091 to use corrected reader. Only publisher remains intended background process; research agents finished. Batch44221 no longer live. Final verifier exec10968 completed168 receipts against84network manifests: percriterion6420158residential references; no full per-route replay or legal qualification claim. Evidence docs/results/normative-national-walking-measurement-validation.json. Country N04 API84ready.

Checks604backendunit/Ruff/mypy311;4index/review/interval integrations plus affected snapshot integration passed;458frontend/fullverify;102ETL. Latest startup/update log /tmp/normative-legacy-read-deploy.log. No commit/push or mobile/paid checks. Next P0 is large physical-view paging/viewport clusters and single-origin route reads; contract work/screens/regional-result-pagination.md. Full goal still incomplete (large full physical GETs, clinical/child population, entrance/municipal and emergency qualifications, further regional legal sources).

Latest user questions answered while continuing the goal: «ну че там» and «как быстро это все пересчитывается». Timing evidence docs/results/normative-recalculation-timing.json:479car successes median1.93s/P90~16.80s/max145.75s;116fresh receipt walk runs median5.53s/P90~21.71s/max74.35s. These include calculation/storage/HTTP. Aggregate historical successful durations~82.5min, full national sequential1–1.5h given as an estimate, not fresh controlled benchmark; excludes known reused KrasnodarN04 from fresh sample. Cached-card0.164s is opening a saved result, not recalculation. Keep that distinction.

Superseded context checkpoint retained:
Current: docs/normative-indices-plan@0c7cb89; no commit/push. Numeric conditional indices deployed8083/API8003; P0 regional index bases. [Checkpoint](../work/normative-session-history-2026-11-12.md#indices-priority-and-regional-walking-pipeline).


## Bounded regional viewer and desktop validation

Implemented/deployed8083/API8003 descriptor, server row/facility pages, single-point reads and viewport grid aggregates; route reconstruction reads only saved point/facility metadata before frozen graph replay. Includes legacy JSON read fallback. Shared DataTable supports external pagination and server sorting. Physical Kurgan now uses regional data; cached qualified pilot data cannot override travel mode. Catalog fallback preserved when no regional measurement exists. Index view does not load full arrays.

Krasnodar N04 run af7636df4c3247a3a99d26af909968ac:526926origins,320465known routes,world aggregates conserve counts. Desktop1440/1920: disjoint pages, search and real720-node route, max observed viewer response53625bytes,0JS/axe/overflow. Deepest sorted page5270 returns26rows/27910bytes; one live observation0.096s, not benchmark. Oversized page rejected422. Evidence docs/results/normative-paged-results-validation.json, scripts .local/normative-paged-desktop.mjs and .local/normative-cluster-browser.mjs (execute via node --input-type=module fromfrontend with stdin).

Negative: initial second-width sorted page503, ClickHouseCode241 at24MBquery because shared total memory pressure; concurrent failing background merge identified as system.metric_log, not own table. Shared settings untouched. Page query now sorts positions before fetching complete columns; later limited desktop passes do not establish elimination of global pressure. Tooltip initially intercepted cluster clicks;24px offset plus browser hover/real click verified Nenets N04zoom4→7 and Moscow N01zoom8→11 with reduced motion,0JSerrors. Regional hover card hidden in physical view so it does not incorrectly show regional 'no data' over known paths.

Correction to prior checkpoint: actual latest84manifest totals are75402464nodes/160134727edges/6337686origins, matching all168receipt revisions/counts. Earlier6420158 and larger graph sums were incorrect for current manifests; their origin is not established, do not repeat them as current counts. Evidence docs/results/normative-latest-walking-networks.json.

Checks: backend611unit/Ruff/mypy321; storageintegration test_regional_view1pass after final SQL change; frontend462/fullverify after final hover-card correction. Final deployed UI passed both large-region desktop widths and both cluster-click cases. ETL unchanged, prior102. Publisher66091 confirmed live; no batch restart. Full objective incomplete: most regional bases/verified inputs/qualification remain. No commit/push. Branch docs/normative-indices-plan@0c7cb89.

Final stand healthy8083/API8003; publisher66091 revalidated live. No original8080 changes. Next: audit remaining implementation plan gates, expand regional legal bases and qualification inputs; shared ClickHouse memory pressure remains unresolved outside this bounded-view change.


## Superseded normative completion audit before bounded regional viewer

# Проверка полного нормативного плана, 12.11.2026

Проверено против исходных шести этапов `work/territorial-indices-plan.md`, текущего журнала `work/normative-implementation.md` и размещения всех девяти услуг в исходном меню карты. **Полный план не выполнен.** Зелёные тесты и работающая карта не подтверждают отсутствующие входы, контингент, эксплуатационные условия или исчерпывающую актуальность правовых оснований.

Предыдущая версия аудита сохранена в журнале сессий, раздел `Superseded completion audit before full fire catalog`. Этот документ описывает текущее состояние.

## Требования и проверяемые доказательства

| Требование | Авторитетное доказательство текущего состояния | Вывод и остаток |
|---|---|---|
| Отдельный worktree, исходная карта, без коммитов/push | `git branch` и HEAD: `docs/normative-indices-plan@0c7cb89`; исходный worktree сохранён. UI8083/API8003 и dev8082/API8002. Девять услуг в исходной группе карты | Реализовано. Работа не публиковалась |
| Этап 1: акты, редакции, исключения и адресат девяти норм, МНГП | Каталог N01–N09, первичные тексты и профильные исследования. Медицинские формы, санитарные переходы, 40/60 библиотек, 10/20 пожарных, муниципальные школьные/остановочные ветки отделены | Частично. Полная цепочка редакций и актуальность применимости ряда оснований не доказаны. Кандидаты не маркируются подтверждёнными действующими условиями |
| Этап 2: подтверждённый пилот N01/N05, затем N03 | По16адресныхзаписей для экстренной/неотложнойкардиологии,2координаты/14пропусков,38 адресов/16 координат МФЦ,26 адресов/9 координат пожарных | Не завершено. Координата здания не подтверждает вход/выезд, нет распределения взрослого контингента и прикрепления по пунктам |
| Этап 3: источники, входы, статус, режимы, версии, пропуски | 1278 записей объектов/профилей. Полный рассмотренный срез 26 адресных заголовков МЧС,9 прежних OSMкандидатов и 17null. Сохранены сырые адресные строки/страницы, хеш PDF и снимки источников. Пешеходная сеть 343523 узла/727804 ребра | Частично. Входы, выезды, полнота работающих реестров, обслуживание, детское/взрослое население и оперативные данные отсутствуют. В текущем каталоге842хеша первичных документов; новый N05-снимок имеет38, N03имеет26.436областных библиотечных записей без первичных байтов; медицинский PDF найден и рассмотрен заново; прочие исторические снимки не переписаны |
| Этап 4: подходящие цели, время/метры, охват и превышения, отдельно мощность | Все 9 физических веток. Типизированная квалификация N01/N02/N03/N04/N07/N09, допустимые цели до маршрутизации, условные пороги, отдельные нечисловые состояния и неизвестный знаменатель. Мощность не подмешивается в транспортный индекс | Частично. Рабочие реестры подтверждений пусты. Положительная квалификация проверена только тестовыми данными. Географический охват N05/N06/N08 не является подтверждением правового соответствия |
| Этап 5: закрытие/восстановление связи и альтернативы | Исходная/изменённая сеть, сохранённые пути, сравнение времён, потерь/появлений путей и охвата при известном знаменателе. Контрольные тесты параллельных альтернатив, направленности, закрытий и привязки подтверждений | Реализованы вычислительные сценарии. Полный эффект в нормативно квалифицированном населении не подтверждён без входных данных. Окупаемость не заявляется |
| Этап 6: контрольные маршруты, исключения, юрисдикции и UI |534 backend unit,51ETL,446frontend,36 правил, выбранная пожарная интеграция; реальный маршрут от депо к вызову и точное восстановление. Desktop1440/1920 показывает первичную страницу, неизвестную координату и документный хеш без JS/axe/overflow | Частично. Предметная проверка маршрутов на местности, входов, состава населения и полноты реальных транспортных ограничений не выполнена. Общая нехватка памяти ClickHouse Code241 ранее наблюдалась и не устранена |

## Что содержат последние сохранённые снимки?

Источник: `docs/results/normative-readiness-2026-11-12.json`, время проверки 2026-11-12T08:30:37.753796+00:00. Проверены метаданные и агрегаты таблиц, а не все браузерные сценарии или юридическая квалификация.

| Показатель | Версия снимка | Точек | Путей в минутах | Путей в метрах | Учреждений | Координат | Хешей документа |
|---|---|---:|---:|---:|---:|---:|---:|
| N01 | normative-v8 | 1235 | 1234 | 0 | 16 | 7 | 16 |
| N02 | normative-v8 | 1235 | 1234 | 0 | 16 | 7 | 16 |
| N03 | normative-v7 | 1235 | 1234 | 0 | 26 | 9 | 26 |
| N04 | normative-v5 | 41236 | 0 | 27577 | 34 | 34 | 0 |
| N05 | normative-v8 | 1235 | 1234 | 0 | 38 | 16 | 38 |
| N06 | normative-v3 | 1235 | 1234 | 0 | 24 | 12 | 0 |
| N07 | normative-v6 | 1235 | 1234 | 0 | 429 | 35 | 0 |
| N08 | normative-v3 | 1235 | 1234 | 0 | 1 | 1 | 0 |
| N09 | normative-v4 | 41236 | 0 | 27578 | 658 | 658 | 0 |

Старые версии не переименованы в v7. Старый пожарныйrun137ac70c89d44d3a991445824f22bd34 сохраняет 9 целей/0 хешей. Текущийrun61737ee8f3d64ef5a1909f80f646fd99 сохраняет 26 целей/26 хешей. Это разные снимки, а не подмена исторических входов.

## Какие источники позволяют проверить новый пожарный каталог?

`datasets/normative-fire-source-records.json`, `datasets/normative-fire-coordinate-candidates.json` и `etl/normative_fire_directory.py`. Фактический PDF197248 байт/13 страниц, SHA256c7710fe218bf522a93bb1af8c0653316ef5c77dea6776a9d55bb5587856ac3d4. Просмотрены страницы 7–11, адресные заголовки 6+8+6+6 на 7–10. 34 ПСЧнеполучилавыдуманныйдом,11 ПСЧнеи 15 улицанепереписаныпоисторическимвариантам. Дата в URL не превращена в дату редакции. Персональные контакты не перенесены. Источник не доказывает полный текущий состав пожарной охраны.

Точный POSTCompose/GETdev, неизменные времена/цели/пороги/население 1235 пунктов относительно предыдущих 9 координат,534 unit / 51 ETL / 446 frontend и 1 выбраннаяинтеграция за 29,19 с. Машинный протокол `docs/results/normative-fire-directory-validation.json`. Ошибка селектора в новом тесте и первый неуспешный build исправлены до обновления контейнеров; повтор всех frontend проверок и сборка прошли. Скрипт desktop сначала использовал неверное имя поля поиска; повтор с именами из словаря прошёл.

## Независимые объекты N03: закрытый программный остаток

В normative-v8 реализованы самостоятельный реестр объектов назначения, явный выбор набора точек, привязка к разрешённым дорожным узлам в250м, отдельный объектный контингент и неизменяемое происхождение в снимке. Произвольный IDsite-42 проходит реальную маршрутизацию на изолированном графе без вызова исходных населённых пунктов. Интеграция сохраняет результат в приватных таблицах ClickHouse и воспроизводит строки/источники/путь после очистки текущего тестового реестра. Таблицы удаляются в finally. Рабочий реестр объектов пуст; положительный нормативный пилот этим не доказан.

563backendunit/Ruff/mypy277файлов,56ETL,451frontend/36правил/типы/lint/build прошли. На реальном Compose GETреестра=[], POSTобъектного режима с явным профилем503, без нового расчёта по населённым пунктам. Desktop1440/1920: пустое состояние, disabledкнопка при заполненном профиле, подпись сохранённого набора не меняется;0JS/axe/переполнения. Регрессионный тест различает исходные4,5мин и сценарные14,5мин в карточке и таблице. Протокол `docs/results/normative-fire-object-validation.json`.

## Что выполнять дальше?

1. Программный путь независимых объектов N03 реализован и проверен. Для реального объектного пилота нужны подтверждённые адресные объекты и контингент; рабочий реестр пуст.
2. Проверенные байты шести дополнительных источников перенесены в784записи; новыйN05снимок сохраняет38хешей. Следующий остаток:436областных библиотечных записей без первичных байтов; медицинский PDF найден и рассмотрен заново, текущая актуальность источников.
3. Измерено и применено ограничение только нормативного reader: память полного чтения82 472строк142,8→96,4МБ, данные точноравны; запрос БД139→271мс. Отказотсортировки не дал существенной пользы, сортировка сохранена. Полные HTTPчтения прошли, при конкурентном пересчёте N09замедлилсядо18,925с. Общее давлениепамяти/Code241остаетсянезакрытым. Протоколnormative-read-memory-validation.json.
4. Для подтверждённого пилота нужны реальные источники входов/выездов, контингента/прикрепления, действующего обслуживания и транспортного профиля. Вопрос команде уже задан, ответа нет. Пустые реестры не заполняются тестовыми подтверждениями.
5. Юридическая текущая применимость и предметная проверка данных остаются условиями завершения. Пока эти доказательства отсутствуют, цель не объявляется достигнутой.


## Уточнение медицинского источника

Первичныескан/официальнаякарточка подтвердили1469от16.10.2025;1169былошибкойчтения. Таблица2полностьюрассмотренана10–14:17адресов,16подходяткаждойформе,плановаяШадринскаяЦРБисключена.32профиля сPDFхешем39737633байта,2геометрии/14пропусков.1278текущихзаписей/842хеша.77ETL/новаяинтеграция1pass/Ruff/mypy279; реальныеN01/N02снимкиv8сохраняют16целей/16хешей,старыефизическиевремена,статусыunknown/населениеnull,POST=GET. Desktop1440/1920недостающаягеометрия/page12/хеш,0JS/axe/overflow. Протоколnormative-medical-directory-validation.json.

П5с3отменяет194от19.02.2024; приложение1с5предусматриваетежегоднуюактуализацию.8страниц/76официальныхкарточекнеподтвердилиисчерпывающуюнеизменность2026года. Этоостаетсяправовымусловиемпилота. Ранееотсутствиемедицинскихбайтовбылоошибочнымпредположением:PDFужеимелсявисследовательскомкэше. Новыегеометрии14адресовещёненайдены; первичныебайты436библиотечныхкарточек/подтверждённыйпилот/Code241такжеостаютсяоткрытыми.


## Пять проверенных адресных совпадений OSM

90ETL/интеграция1/Ruff/mypy279. ДлякаждогоN01/N02теперь7координат/9неизвестных. НовыйPBFсрезпроверяетcity/streettype/street/house+уникальностьконтура. Макушинос2зданиямиотклонено,несмотрянаbankтегуодного. Н01c20c49e2ab474c0c8aabadc87f394232/N0260e182f5def348208780f4867e78d861:790уменьшившихсявремён,нетувеличений,всенормативныестатусыunknown/взрослоеPnull. POST=GET/контрольмаршрутаточен. Desktop1440/1920новаянеподтверждённаягеометриясOSMссылкойиотдельнымPDFхешем0JS/axe/overflow. Артефактnormative-medical-coordinate-validation.json.

ПервичныйкоординатныйPBFхешзафиксированвисточнике/наборе,ноотдельноеполевснимкахучрежденийещёнепроведено. Далее: этоткоординатныйслед,9оставшихсяадресов,436библиотечныхпервичныхбайтов/currentlegal/подтверждённыйпилот/Code241.

## Расширение после замечания о масштабе

Каталог теперь включает279736OSM-объектов в84территориях карты. Отдельный региональный автомобильный API/хранилище/UI/маршруты реализованы для6услуг. Сохранённые физические значения остаются видимы при неизвестном нормативном статусе. Граница готовности: это не квалификация услуг по региональным актам, не пешеходная сеть для всей страны и не пожарное реагирование. Московский контроль и точное сравнение оптимизации: normative-regional-road-validation.json. Массовая подготовка находится в процессе; её завершение ещё не проверено. Следующий программный шаг: территориально привязанные пешеходные сети и модели остальных3услуг, затем проверка региональных источников и допустимых объектов.


## Employment directory integration and new regional index bases

Previous goal turn was progress: bounded viewer implemented/deployed/verified. This turn: repaired missing Kurgan regional N06 by joining current imported facilities through explicit regional_directory_memberships, not names or hardcoded region branches. New DDL infra/clickhouse/normative-regional-directories.sql and data datasets/normative-regional-directories.json; import_regional_directories.py validates known region/category, explicit existing ID/service, duplicates and exact source URL/hash.24memberships imported,24facilities/12coordinates/24primaryhashes/12coordinatehashes preserved in saved snapshot. Private integration confirms OSM+directory union, missing geometry and no region/category leak. Initial f-string parameter escaping/F821 and incorrect shell cwd were corrected before checks/deploy; no original-tree changes.

N06 Kurgan run033a7c1119e04175a1bcff6bd2d42d5d:1234reference points,1233knownpaths,767within60min, population776633/within661146 =>85.1297846%. Independent SQL sums match API. Control origin37624456106→employment-11185dfb1d63:173.8217609959min,116network vertices, saved cost replayed, sourcehash preserved.

Added two Krasnodar bases (23total): N06=90minutes, transport unspecified, car scenario conditional64.6120694% /3772229of5838273residents, existingrunfeaa58bddd394ffb83cc6148ae666a8f; N05 explicitnot_regulated. Official2301202507170001, order78edition87dated11.07.2025, table11/p2.9.1physical27/printed25, PDF4392309bytes SHAf466fdee1348ea4f3def66ff49811d86597230297b85c91c54ec9bde961b4547. Originalpage inspected. Rostov N05explicitnegative excludescapital, not generalized/imported. Tatarstan/Tyumen no provenN05/N06, no inventednegative. Researchagentfinished, note copied work/research/regional-index-bases-south-volga-tyumen.md.

UI shows calculation date and population numerator/denominator separately from pointcounts. Index-specific citation label handles full act names. Full frontendverify462passed; finalUIdeployed, all6cases (KurganN06/KrasnodarN06/N05×1440/1920) after source-link/camera/networkidle readiness passed0JS/axe/overflow and0full-data initialrequests. First browser selector incorrectly expected an EmptyState heading and screenshots were premature; corrected verification. SQL diagnostic alias initially collided, corrected without app change. Evidence docs/results/normative-employment-indices-validation.json. Backend611unit/Ruff/mypy322,110ETL,1newrealstorageintegration passed. No OpenAPI change.

Live all9×84 API audit:266ready conditionalregion/service pairs; NOT percent plancompletion. N01/2/4 each84; N03=1;N05/6/7/8 each3;N09=1. Updated work/audits/normative-completion-2026-11-12.md; older audit archived above. Real qualification facts files remainempty. Full goalincomplete; no commit/push. docs/normative-indices-plan@0c7cb89. Runtime8083/API8003healthy, publisher66091 confirmedlive, batchesfinished.

Important next step: new official SP42.13330.2026 discovered by researchagent, now finished. Note copied work/research/federal-stop-accessibility-sp42-2026.md; fullPDF.local/research/sp42-2026-minstroy.pdf,2230247bytes/339pages, SHAb4d980a6038a6b228d75b31b0912851a1eea5261905a786c907000779c07db12. Physical166–167/table8.12 requires pavilion↔farthestparcelboundary, opposite-direction stops and pedestrian network. Proposed measurement identifier stop_pavilion_to_farthest_parcel_boundary_opposite_directions. House500/800m and optional47-subject400/700m conditions, not old2016climate defaults. School1000m is distinct. §1.3 federalfallbackwhere regional/local absent; mandatory applicability unconfirmed. Do NOT import newfederalbasis with old regional-walk-v1 nearestpoint→anyPOI, or issue itspercent. Next implementation: typed measurement requirement/compatibility guard in IndexBasis/domain/usecase/map/cache/API/UI, then import source as incompatible-model state; actual pair/boundary model and source data still needed. No such guard/source import implemented yet; currentregionalKurganN09basis unchanged. If adding IndexBasisfields, restart publisher66091 withnewcode BEFORE newrequired-definitionbasis import (oldwatch would ignore field and publish wrong summaries). Preserve soleoriginal8080 untouched.


## Measurement compatibility and regional coverage expansion

Latest steering: «ну что там, уже 16 часов прошло, где все мои индексы в каждом регионе». Answered that requirement is unmet; no invented ETA. Live9×84 audit now269 conditional numeric pairs,27basis records: N01/02/04=84each,N03=1,N05=4,N06=5,N07=3,N08=3,N09=1. No confirmed regulatory pilot. Branch docs/normative-indices-plan@0c7cb89; no commits/push; original8080 untouched.

Implemented/deployed typed MeasurementDefinition in basis/domain/measurement/model/head/cache/map/API/UI. New SP42.13330.2026 basis requires stop_pavilion_to_farthest_parcel_boundary_opposite_directions; existing regional-walk-v1 actual single_reference_point is incompatible.83territories show measurement_incompatible without numeric result, Kurgan keeps its separate local conditional basis. Definition mismatch rejected in formula/cache/publisher/route replay; missing legacy tags default single_reference_point. Matching future measurement can work; no permanent criterion blacklist. Latest metadata helper reads only id/saved_at/definition, never giant legacyJSON for incompatible requests; compatible miss freezes head.run_id and validates returnedID/definition. Actual parcel/pair model and inputs remain unimplemented. Required/current measurement explained in RU card; physical model still viewable with599vertex route.

Backend619unit/3affected realstorageintegration; frontend462/ETL110passed earlier this continuous feature. Current desktop reruns:12cases KurganN06/KrasN05/N06/StavN05/N06/KirovN06×1440/1920,0JS/axe/overflow,0initialfullarrayrequests. Compatibility2widths also passed again, source and physical mode, route599vertices. Proof docs/results/normative-measurement-compatibility-validation.json and normative-regional-index-expansion-validation.json. Single-sample metadata API0.0447/0.0135sec,1764bytes each; not benchmark.

Added Stavropol N05/N06=90min (532/10.10.2022, official2601202210120001, fullPDF SHAcefca5676fbdb099984e5516400b4bf1dae6b9c8e37647669ada5142dd979183),760points percriterion. Population2907593, within2372327/1131134 =>81.5907522%/38.9027625%. Added KirovN06=60min (523-П/29.11.2024, official4300202412020012, table9row2.9PDF46printed43, fullPDF SHA705990a3b5ee4960b4cd7836bf0c46065b838c38eb15d565c834575046938833):4245points/4244paths,population1153680,within715984 =>62.0608834%. Transport unspecified in acts; car model conditional, unverified POI/operatingprofile. Independent sums from stored legacy payload match API. First SQL attempt alias collision, then typedrow query returned0 because these runs are legacyJSON; no fakeSQL validation claimed.

Publisher81819 (revalidate before signalling), sole watch on exec57674; publication log shows Kirov published. Runtime8083/API8003healthy. Source research three28region partitions has limited verified profiles, source discovery is not completed legal coverage. Notes in agents’ worktrees, do not blindly import scoped profiles/km thresholds or claim negatives from missing acts.

New actual data opportunity: production trudvsem.ru/czn official anonymous region map. Root downloaded czn.html,regionsList91 and26Kemerovo centers under .local/research/employment-national. GET?regionCode ignored: rejected file renamed region-query-ignored.rejected.html (actual42/requested26). TLS verified with certifi.where(); no TLS bypass. Agent medical_source_currentness now successfully selects via CookieJar and exact AJAXheaders POST/iblocks/region_change/change?code=...; actual selected26 verified. Agent acquiring84official region directories in own worktree and single work/research/official-employment-national-directory.md, rawbytes/hash/scope, productfields only name/address/lat/lon. Not yet ingested. Existing facilities MergeTree + memberships not version-safe for wholesale replacement; prefer immutable directory snapshots metadata-last and official public-service targets, avoid append duplicates/private OSM agency contamination.

Pending optional user preference sent asynchronously: only applicable-act indices vs additionally comparative model indices where no legal threshold; no answer, no comparative indices authorized/implemented. Full plan incomplete. Next prioritize real national directories and compatible legal scopes; no further provenance-only UI detours.


## Session memory compaction after regional expansion

Current docs/normative-indices-plan@0c7cb89, no commit/push. Runtime8083/API8003healthy; publisher81819live, revalidatePID.27bases/269conditional scores; N01/02/04=84each,N03=1,N05=4,N06=5,N07=3,N08=3,N09=1. Measurement-definition guard deployed;83federalN09scores blocked for wrong model, no claimed compliance. StavN05/N06=81.6%/38.9%,KirovN06=62.1%, verified stored sums and12desktopcases. National official CZN acquisition now running in medical-source-reviewworktree; not ingested. Full goal incomplete. [Checkpoint](../work/normative-session-history-2026-11-12.md#measurement-compatibility-and-regional-coverage-expansion).


## National scenario indices after direct calculation request

Previous goal turn: progress; importedKirov and verified269conditionalnumericalpairs. Latestusersteering preserved: «просто уже посчитай индексы и все». Proceeded with explicitly labeled comparative scenarios, no new question. Mainmap now754/756numericpairs: N01/02/03/04/05/06/07/09=84each,N08=82;352readyconditionalbasis,402scenario_ready. Remaining2N08 are Nenets/Chukotka with no loadedterminaltargets; do not fabricatezero or applicability. Full legal/pilot/stop-pair plan still incomplete; goal remains active.

New domain scenario_index policies and reference_index_values share formula with legal indices. ScenarioIndex stored separately in plexus_normative.scenario_index_summaries, frozenrun/policyhash/measurementdefinition checked; no full measurement rows on card requests. API RegionalIndex.model_index is separate, original legalbasis/status remain unchanged. Map uses scenarios only where legal-basis numeric result unavailable, labels scenario_ready. N09regulatory incompatibility guard preserved. N03card explicitly shows40km/h model assumption. Newsource files underdomain/usecase/repository/clickhouse, etl/calculate_scenario_indices.py --watch. SQL alias-placement and ambiguous returnedcolumn names corrected before deployment; zero-match sumIf NULL now coalesces0 only with knownpopulation.

Background official CZN acquisition completed84/84,2470records,325artifactsSHAvalidated. Report copiedwork/research/official-employment-national-directory.md. importer etl/import_official_employment.py --source-root /Users/savelij/projects/casechamp-medical-source-review verifiesraw/cleanhashes, actualregioncode, all84IDs. Immutable service_directories header-last/typedfacilities, private storage check verifiesunpublishedrows invisible/newfullsnapshot replacesold/corruptheader fails. Officialsource overrides OSMapemployment instead of mixing privateagencies. Exactduplicates64removed;2406records/2229located. Out-of-bbox or unclear-nameprofiles retainrows withoutcoordinates; no guessedcoordinate repairs/entrances/active status. Source rawbytes remain in source agent worktree; own docs/results/normative-official-employment-import.json retainsmanifest.

Employment batch .local/official-employment-measurements.json terminal84attempts/83success; Altai64officialdedupnames allsocial-protection profile ->0routablecoordinates; correctly503no target, previous datedOSM index remains. Newofficialrun independentreplayBuryatia saved56.167418546min/74vertices matchesroute exactly, officialsourcehash preserved. Firebatch .local/fire-national-scenario-results.json terminal84unique200 with40km/h assumption; firstdeployinterrupted11calls, retryfilledall. Never restartedonlybecauseobservationtimeout.

Routing now selects existingweightedmultisource algorithm for2+targets (previously33+), samecost/directions/approaches verifiedbyexistingindependentsearch tests and live routecontrol; avoids repeatedcountrywideDijkstra pertarget. Backend622unit/mypy332/Ruff passed,111ETL,462frontend/fullverify,3newaffected realstoragechecks passed. Desktop6cases N05Altai/N09Kras/N07Vologda×1440/1920 passed0JS/axe/overflow/initialfullarrayrequests. Finalfire-speed annotation deploy pending atcheckpoint; revalidatehealth/browser oncefinalbuildfinishes. No mobile/paid checks/commit/push.

Processes: originalnormpublisher81819and scenario publisher13395 (revalidatebothbeforeanysignal), latter exec43638. Both livewatches; allcar/walk/fire/employmentbatches terminal. LatestAPI/UIbuild exec26210(log.local/scenario-final-deploy.log) maystillstartup~40sec; inspectauthoritativestatus. Mainfeature8083/API8003only, original8080 untouched. Proof docs/results/normative-national-scenario-validation.json and livecoverageupdated. Next: finaldesktopfire-speedcheck, updatecontextwithcurrentcounts, then continueactuallegalqualification/fullplan; do not claimallnormativeindices complete.

Final verification: finaldeploy26210terminalsuccess, APIhealthy/UIrunning.10desktopcases across1440/1920 (addsfire40km/h annotation and newofficialCZN_NAO) passed0JS/axe/overflow/fullarrayrequests. Fresh8083proxy9×84audit754numbers,2emptyN08catalogs directlyverified. Updatedfinalproof. Publisher81819/scenariopublisher13395 confirmedlive; no batchactive. Final622unit/mypy332/Ruff, frontend462/fullverify,111ETL,3affectedstoragechecks green. Fullgoal stillincomplete; nextactuallegalqualification, inputcompleteness, parcel/stop and pilotgates, not completedbyadditionalnumbers.

Continuation: previous goal turn classified progress (754numericpairs, officialdirectories, actualbatchresults, UIchecks). New action: primary-source research delegated under researchskill to national_service_sources in its own worktree for missingN08Nenets/Chukotka. Secondary lead Chukotka539/22.09.2025 describes absent INTERREGIONAL terminalcomplexes; not imported or generalized. Primarytext/SHA/profile/currentness pending. Corrected old walking-publication paragraph in plan to explicitly historical; current84networks unchanged. Goal remainsactive, no blocker threshold met.

Added etl/validate_scenario_indices.py to reaggregate all current scenario summaries from frozen immutable measurements, all fields compared. Firstrun failedsharedClickHouse241whilelegacy payloadread; fixed producer SELECT max_threads=1,max_block_size=1 (previous rawrequest lackedlimits). Retryexec38876live atcheckpoint; inspect samehandle/log.local/scenario-reaggregation-validation.log before claimingpass or restarting. Primarymissingterminalresearch remainsactive. No completionclaim.

Reaggregationexec38876terminalexit0:502/502current scenario summaries matchallstoredmeasurement/policy/baseline/scenariofields,0mismatches. Proofdocs/results/normative-scenario-reaggregation-validation.json linkedfromnationalprotocol. Backgroundresearchnational_service_sourcesrunning(primaryChukotka539publication8700202509240004located), medical_source_currentnessrunningAltaiindependentCZNcatalog: validatedproviderDOMczn_map hasonlyonevar data, sourceitselfpublishessocialprotectionnames; notparserselectionbug. No blocker/no completionclaim.

Continuation: prior turn progress (completed502summary reaggregation/evidence). Sourceagents medical_source_currentness and national_service_sources confirmedrunning via liveagentstatus; finalMDnotyetcreated, no assumptionofcompletion. After boundedlegacy-readfix reran111ETLtests; log.local/scenario-reaggregation-etl-tests.log. Documented actualreadonlyreaggregationcommand and fullprooflink in docs/normative-accessibility.md. Fullgoalactive; usefulprimaryresearch remainsrunning.

Continuation: originaluserattachmentimage-1.png visuallyinspectedagain; requirementisindicesinsideoriginalmapmetricselector, notseparatepage. Currentimplementationusesoriginalselectorandexistingmap. SourceagentsstillresearchingactualAltaiCZNandterminalprofiles; no newdataclaim. RootinspectedprimaryChukotkaofficialsheet13/printed12 andsaveddocs/results/chukotka-interregional-terminal-source.json previous turn; scopelimitedinterregionalabsence, neverimportedasuniversalzero.

ActualAltai correction: primaryportal.22trud.ru/czn rawSHAa924848a78c69cd3db48babe620ae9e995dc5d3b63a1aeff08b0b5bed53bfa92,65published/visible exactunique CZN records with65accepted officialcoordinates. Newetl/import_altai_employment.py validatesprimarySHA,reusesbbox/profileguard, metadata-lasttyped snapshot; generationd16ca0010f0a4c2ba4c5aa2ded78b5ec overridesbadtrudvsemregionaldirectory. APIrecalculationexec67526started, receipt.local/altai-official-employment-receipt.json; verifyterminal/latestscenarioheadbeforeclaimingnewpercentage. Proofdocs/results/normative-altai-employment-import.json. Sourceagentownsraw/normalizedJSON, finishMDpending. No legalcomplianceorentranceclaim.

Altai67526terminalsuccess: run520c51c4e7e94ad6ac07312f7fc276e2,1604origins/1604paths/65officialtargets; scenario60min97.980734606938%, publishedandAPIrunIDasserted. SourcecleanSHA8e575b91fa647a9ed83d3950b817cf91fa4efa8456a705e8aa58186449c6afa0nowvalidatedbyimporter aswellasrawSHA. Sourceagent finished65raw→cleanmatch,39legalvsactualaddressdifferencescorrectlyusespublishedAddressAny. Reportcopiedwork/research/altai-employment-directory-correction.md. UpdatedcurrentCZNcoverage/plan; desktopexec69559runningtwoAltaiwidths, revalidatebeforeclaimingUIpass. Historical83/84failureproof remainshistorical; newerAltaiimportproof supersedes it.

Altai69559terminal0:1440/1920actualnewindexcardpasses0JS/axe/overflow/fullarrayrequests; proofupdated. RepeatimportwithbothrawandcleanSHAvalidatedreusesexistinggeneration(noadditionalpublication). CurrentofficialCZNcalculations84/84; fullgoalnotachieved(legalinputs/pilot/parcelmodelremaining).

Imported28thlegalbasis: KBR83000000N06explicitnot_regulated, original173-ПП26.09.2019table11PDF25visualverified;fullprimaryPDFSHA9315f4b2e52036fd8044bd1fe0346e66523c256360226eb701cd524fcc27370f. Currentnessunconfirmed, onlyregionalCZNscope. ActualAPIassertstatusnot_regulated, normativescenarioempty, separatecomparativescenario retained. No newpercent/no sourcecurrentnessclaim. Existingcoverageevidence27basesnowhistorical; updatecurrentmetadatatonextcheckpoint.

29thbasisKBRN08: independentlyrenderedofficialPDFpage23, table1p1.5.1explicitnotestablished; scope regional/intermunicipal terminals, notallstops; original2019currentnessunconfirmed. ImportedandactualAPIbothKBRN06/N08assertnot_regulated withseparatecomparativevaluesretained. Proofdocs/results/normative-kbr-legal-bases-validation.json. Currentcontext/basecount29;754numbers unchanged.

30thbasis MagadanN06: fullofficialPDFSHA7a87b1d77a8315407114c104f542e3dd29b2ca51a1d351df9521a8ce516459c9, visuallyverifiedtable11row2PDF14. Intervals30urbanokrug/60municipalokrug, territorialCZNprofile, unspecifiedtransport. APIlocal_selection_required, normativevaluesempty, independent60minscenario retained. Proofnormative-magadan-employment-basis-validation.json. NextUIgap: municipality_type municipal_okrug lacks dedicatedtranslation/mapkey, currentlygenericregionfallback; addaccuratelabel before callingUIcomplete. No newlegalpercentorcomplianceclaim.
