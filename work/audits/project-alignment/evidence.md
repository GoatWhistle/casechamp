# Проверки 9 ноября 2026

Исходная ревизия: 81b6524f5724032bc707b2433eca6713594607ce, main.

- Через FastAPI TestClient с create_app() и настоящим JsonAtlasRepository: GET /api/v1/overview → 200, regions=82, settlements=155412, links=997; GET /api/v1/index → 200, status=missing; GET /api/v1/regions/93000000 → 200, links=7, hansen=null; неверный season → 422 validation_error. Это проверка API и файлов, не браузерный стенд.
- frontend/atlas/public/indices.json содержит []. data/ отсутствует. Экспортёр frontend/atlas/scripts/export-indices.py существует, требует idx_region из DuckDB.
- Из atlas.json: 997 связей, у всех есть строка source_url; у 528 нет freq_per_week, у 61 нет source_date. Наличие URL не доказывает актуальность или правильность записи. Разбиение API: 67 связей с неизвестным сезоном.
- Изолированно выполнена настоящая функция palma из AST etl/indices.py с numpy, без запуска ETL: x=[1,1,1], w=[45,45,10] → 10000000000000.0. При равных значениях верхние 10% / нижние 40% дают 0.25. Функция не делит вес НП на границах квантилей. Первая попытка в backend-окружении завершилась ModuleNotFoundError: numpy; повтор через uv run --no-project --with numpy успешен.
- min(168/f/2,24): f=1,2,3 дают одинаковые 24 часа; f=4 → 21, f=7 → 12. При полупериоде Hansen 2 часа только ожидание 24 часа уменьшает вклад цели в 4096 раз. Это следствие формулы, не измерение реального спроса.
- Git ancestry: 06b33e5, 20beaba и 7a51d72 — предки HEAD. Локально main, remote origin/main. Слияние сохранило историю, но не устранило различия моделей.
- Браузер, полный ETL и достоверность всех внешних источников в этом аудите не проверялись. Числа корреляций и национальных индексов из docs/indices.md не перевычислены: нет расчётной базы. Предыдущие проверки слияния: frontend 372 теста и verify прошли, backend 106 тестов/Ruff/mypy прошли; EDA validate.py не прошёл из-за отсутствующего raw CSV ZIP.

- Повторный `cd backend && uv run pytest tests/unit -q`: 106 passed.
