# Муниципальная демонстрация

Сборка: `python3 presentation/municipal-demo/build.py`.
Результат: `presentation/plexus-deck.html`.
Исходник: `~/Downloads/Telegram Desktop/plexus-deck.html`; не изменяется.

Сохраняются встроенное приложение, React-чат, MapLibre, упакованные тайлы,
шрифты, курсор, клики, печать и движок анимаций оригинала.
Ширина чата — 352 вместо 480. Мок заменяет функцию получения ответа:
короткий ответ передаётся сразу, без подключения к модели и ожидания.
Сценарии и новые слои карты определены в `reference-scenes.js`.

Данные: границы муниципалитетов и сохранённые показатели из `prepare_data.py`.
Дороги: OSM `data/additional/stavropol/raw/north-caucasus-261107.osm.pbf`,
выборка `extract_roads.py`, результат `roads.json`.

Закрытие полосы — иллюстративный сценарий: 2 → 1 полоса, поток 1500 авт./ч,
ёмкость 1800 авт./ч на полосу. Время вычислено по BPR при фиксированном потоке.
Красная волна обозначает последовательность визуального пересчёта,
не моделирует распространение очереди. Точки на участке — места проверки,
не рассчитанный прогноз пробок. Региональный эффект не придуман.

Управление оригинала: стрелки, R — повтор, F — полный экран.
Проверка: `node presentation/municipal-demo/verify-reference.mjs`.


### Presentation-only update, 2026-11-13

User: «убери шапку с переключением чат / сводка / сценарий».
Changed only the HTML presentation tooling/output: `presentation/plexus-deck.html`,
built from the unchanged Telegram Downloads original. Original app/chat/MapLibre,
cursor, typing and motion engine preserved; chat width352; mocked immediate replies;
Stavropol municipal/social/one-lane scenes. Presentation tab header hidden.
Branch main, observed SHA dd95343. Static10frames, original motion parity, live typing/replay
verified; no external requests or browser errors. Standard deck build/speech check passed
(the separate legacy7-slide deck). Details: `presentation/municipal-demo/README.md`.
Road effect is illustrative, not a measured congestion or index forecast.

## Кадры дорожного сценария

`render-road-frames.mjs` заранее снимает четыре состояния исходной карты.
`road-frames/` содержит базу, перекрытие полосы, цветовые изменения и точки.
Сборщик встраивает изображения в HTML. `road-film.js` использует только готовые
изображения, трансформацию камеры, проявление и короткие подписи.
В дорожном проходе нет изменения GeoJSON или сборки дорожных слоёв на ходу.
Ответ начинается сразу и появляется последовательно, по словам (110 мс).
Проверка: `node presentation/municipal-demo/verify-road-film.mjs`.
Цветовые изменения и три точки — иллюстрация мок-сценария, не прогноз трафика.

Муниципальные сцены 2.1 и 4 приближают карту к границам Александровского округа.
Обзор33муниципалитетов сохраняет общий план края. Камера оставляет место под
карточку результата; правый отступ не дублирует уже выделенную ширину чата.

Выбранная территория имеет белый контур-подложку и синюю обводку: край на
общем плане, Александровский округ при приближении. Переход индекса3→3.1
сохраняет исходную хореографию без размытия большой SVG-карты. Удалены пустые
ожидания после завершения анимаций (18,6→8,2с;17→3,9с). Адрес#3.0 поддержан
как вход в первый кадр индекса. Замеры: `index-performance.json`.

Карта исходной анимации индекса заранее снята в `index-map.png`.
`index-transition.js` подменяет только её сложное SVG-содержимое готовым кадром
перед переходом3→3.1; движение, отдельные точки и график сохраняют исходную
хореографию. Кадр декодируется заранее. Пользователь разрешил использовать
готовые качественные рендеры во всех тяжёлых сценах; курсор и текст остаются живыми.

## Пояснения и формулы

Критические точки получают номера1–3 и по очереди поясняют место проверки:
въезд/очередь, сужение/скорость, выезд/перенос перегрузки. Затем появляется
условное действие, не обещание рассчитанного улучшения. Пульсация связывает
номер на карте с карточкой. Точки демонстрационные.

`formula-scene.js` показывает четыре формулы с примерами:100/50/25% веса рынка,
взвешивание по населению,7из10точек=70% и2→1полоса. Пример70%не является
показателем Александровского округа. Карточки и их элементы появляются
последовательно. Запросы демосцен печатаются25,5символа/с вместо40;
остальные вызовы исходной печати замедлены на15%. Ответ начинается без паузы.
Проверка: `verify-explanations.mjs`, результаты в `explanation-validation.json`.

## Последовательность края и муниципалитета

Первый запрос запускает общий план края с его обводкой и нейтральными
муниципальными границами. Проход ждёт завершения движения камеры и ответа.
После короткого общего плана печатается второй запрос; в это время выбран край.
Только отправка второго запроса выделяет и приближает Александровский округ.
Его карточка появляется после приближения и ответа. Повтор восстанавливает
эти состояния. Проверка: `verify-region-sequence.mjs`.

Карточка Александровского округа появляется за1,8с; индекс нарастает0→84,12
за2,4с, разница0→−15,04за2,2с с небольшим сдвигом старта. Табличные цифры
сохраняют ширину разрядов. Статический режим сразу показывает итоговые значения.
Проверка: `verify-count-up.mjs`, `count-up-validation.json`.

## Новый пример доступности МФЦ

Социальная сцена заменена на Новоселицкий округ, `osm-relation-1030124`.
`social-example.json` содержит11опорных точек из сохранённых измерений N05,
связанных через `point_ids` муниципального агрегата. Пять поездок >120мин:
Артезианский130,7; Журавское122,3; Китаевское122,9; Падинское125,0;
Щелкан149,6. Остальные6точек не превышают120мин. Цвет: красный>120,
зелёный≤120. Это поездки на автомобиле до ближайшего известного каталогу
МФЦ, не доказательство отсутствия неучтённых учреждений и не доля жителей.
Карточка больше не использует дробь или P90.

`demoStartScene` явно создаёт новый чат перед первой репликой каждой
продуктовой сцены. Смена темы и повтор не накапливают сообщения.
Проверка трёх повторов: `verify-social-reset.mjs` и `social-reset-validation.json`.

В пустых чатах презентации скрыты приветствие с иконкой, предложенные вопросы
и недавние разговоры. Поле ввода и текущая переписка остаются.


## Municipal improvement scenario, 2026-11-13

Added beats 5.2 and 5.3: Kochubeyevsky municipality, modeled bottleneck on OSM way 235963363 (Kavkaz), then one added lane per direction. Prepared map frames retain the municipality boundary. The proposal, added lane, green road and index appear sequentially, with original mock chat/cursor. No runtime calculation or model call.

Evidence: `improvement-stavropol/report.json`, `prepare-improvement.py`, `improvement.json`. Both assignments converged (relative gap below 0.0001), identical synthetic demand x1.3 and served demand. Population-weighted accessibility uses 45 origins (76,824 residents) and 157 markets in the snapshot, decay half-life two hours. Fixed baseline accessibility normalized to 100: after 101.73034715928462. This is explicitly a scenario index, not the nationally normalized published municipal index. Selected corridor maximum demand/capacity: 1.4168188897 → 0.7113972386. Construction feasibility and cost not assessed. The rendered red road represents modeled overload, not observed congestion.

Fullscreen sizing intentionally unchanged at user request «оставь так крч». Cover wording and high-resolution index-map asset retained from previous edits.

Visual refinement: scene explicitly enables the original product/chat layer. Zoom 2.2× onto the critical road before proposing the extra lane; zoom back to the municipality before revealing the compact index result. Use «трасса „Кавказ“» in narration and labels. Lane diagram now correctly shows one existing lane plus one new lane in a direction (snapshot capacity 1,800 veh/h). Cards no longer span the entire map. `verify-improvement.mjs` checks final counters, map state, chat visibility and replay deduplication; screenshots in `reference-shots/improvement-*.png`.

Slide 6 layout repair: constrained five-column grid fits the stage, answer wraps normally, and broken ranking substitution replaced with «Индекс края: 99,15. Рассчитан по дорожной сети.». Existing graph/answer choreography retained. Verification screenshot: reference-shots/slide-six-fixed.png.

Latest refinements: improvement starts on a neutral pre-rendered map; red layer fades in only in the post-send callback. Empty chat shows the existing product mark centered above the composer and hides it when the first message appears. Result shows before/after load (142%, overload42%;71%, reserve29%) and modeled corridor travel time averaged across the two directions:24.6→18.3minutes, saving6.3minutes (same saved edge-hour outputs). Beat6.1 «Каждое число можно проверить» removed; old hash redirects to6.

Service-accessibility animation added as beats4.1–4.3 after MFC. Alexandrovsky: N01 19/21 within60min driving (90.5%); N04 35/383 residential reference points within500m walking (9.1%); N09 166/383 within500m walking (43.3%). Sources and selected point geometries: services.json, built by prepare-services.py from municipal export and hashed measurement snapshots. Indicators use point shares, not population shares; physical medical access does not establish specialist availability. The three counters/bars reveal sequentially with prepared point maps, red outside threshold/green within. Service limits are retained under the map. No runtime model/API calls.

At user request removed the improvement-scene bottom «Модельный расчёт» plaque and the «Расчётное время · среднее по двум направлениям» subtitle; computation method remains documented here and in improvement.json. Travel-time numbers unchanged.
