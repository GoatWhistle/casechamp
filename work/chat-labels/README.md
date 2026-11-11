# Подписи сравнения перекрытий

2026-11-11, feat/map-first-ui HEADcdb2c2e.
Ошибка: useCalculationJobs сортировал случайные ID; исходное сообщение не передавалось
в автоматическую интерпретацию, а saved rows не содержали road_names.
Поэтому «первым» становился более тяжёлый составной вариант, хотя пользователь запросил
его вторым. Обновление stress event также перемещало job в конец массива.

Проверены сохранённые результаты API8007 без новых расчётов:
- bb7598613f42450faeefde22aa23d740: М-10,2431segments, max delay212.23808883834863min.
- 8ab724dfe43f4ee99c9e5dd328655b0d: М-10+М-11,3982segments, max delay519.8348821703985min.
- Все way_ids первого входят во второй. Названия подтверждены geometry.names API.

Исправлены порядок запроса и обновлений, UI получает подписи из geometry.names,
review prompt получает road_names и запрет заменять названия порядковыми вариантами.
Старый сгенерированный текст не переписан; его первый вариант был М-10+М-11.

Проверки: frontend verify476tests, backend Ruff/mypy397unit tests passed.
uv cache недоступен в sandbox; проверки проведены установленными .venv/bin инструментами.
Браузер1440 на реальных saved jobs: errors=[], обе дорожные подписи видны, без model calls.
Скрипт browser.cjs, screenshot desktop.png. Результаты расчётов и формулы не менялись.

Backend runtime: очередь завершилась, API8007 корректно перезапущен, PID78464,
health200. Конфигурация .env.analytics, GRAPH_DIR=root/data, CHAT_ENABLED=true,
ROAD_WORKERS=6. Лог /tmp/plexus-chat-label-api.log. Новая интерпретация с моделью не запускалась.
