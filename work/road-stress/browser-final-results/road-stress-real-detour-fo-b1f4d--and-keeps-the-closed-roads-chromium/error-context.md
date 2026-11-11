# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: road-stress.spec.ts >> real detour form renders both paths and keeps the closed roads
- Location: e2e/road-stress.spec.ts:57:1

# Error details

```
Error: expect(locator).toBeVisible() failed

Locator: getByText('До закрытия', { exact: true })
Expected: visible
Timeout: 10000ms
Error: element(s) not found

Call log:
  - Expect "toBeVisible" getByText('До закрытия', { exact: true }) with timeout 10000ms
  - waiting for getByText('До закрытия', { exact: true })

```

```yaml
- link "Перейти к содержимому":
  - /url: "#main"
- main:
  - heading "Карта транспортной связанности" [level=1]
  - application "Карта регионов России":
    - region "Map"
  - link "© Участники OpenStreetMap":
    - /url: https://www.openstreetmap.org/copyright
  - button "Приблизить"
  - button "Отдалить"
  - button "Вся Россия"
  - text: Показатель
  - combobox "Показатель": Доступность рынков Hansen
  - text: Режим транспорта
  - combobox "Режим транспорта": Базовая сеть
  - group "Сезон":
    - text: Сезон
    - radio "Лето" [checked]
    - text: Лето
    - radio "Зима"
    - text: Зима
  - figure "Доступность рынков Hansen":
    - button "Доступность рынков Hansen" [expanded]
    - list:
      - listitem: от 4,00
      - listitem: от 10,00
      - listitem: от 30,00
      - listitem: от 55,00
      - listitem: от 80,00
      - listitem: от 120,00
    - paragraph: Нет данных
    - checkbox "Дорожный граф" [checked]
    - text: Дорожный граф Паром
    - paragraph: "Аэропорты: 285"
  - complementary "Панель карты":
    - button "Переместить окно чата": Вопрос к данным
    - button "Мои чаты"
    - button "Новый разговор"
    - button "Развернуть чат"
    - button "Закрыть чат"
    - group "Панель карты":
      - text: Панель карты
      - radio "Чат"
      - text: Чат
      - radio "Сводка"
      - text: Сводка
      - radio "Сценарий" [checked]
      - text: Сценарий
    - group "Анализ дорог":
      - text: Действие
      - combobox "Действие": Ручной сценарий
      - region "Стресс-тест дорог":
        - heading "Стресс-тест дорог" [level=2]
        - paragraph: Закройте дорогу и проверьте последствия по всей стране
        - button "Сохранённые стресс-тесты"
        - status: "Расчёт завершён: 180 из 180"
        - paragraph: "Потеряли связь с внешними городами-рынками: 169 пунктов"
        - button "Как читать результат"
        - button "Показать затронутые регионы"
        - paragraph: "Регионов: 82. Населённых пунктов: 154 899. Жителей в них: 127 754 656"
        - button "Сравнить маршрут"
        - text: Затронутый регион
        - combobox "Затронутый регион": Все регионы
        - button "Показать пункты на карте"
        - list:
          - listitem:
            - strong: деревня Будовка
            - text: Потеря связи со всеми внешними городами-рынками
            - button "Выбрать пункт"
          - listitem:
            - strong: поселок Выползово
            - text: Потеря связи со всеми внешними городами-рынками
            - button "Выбрать пункт"
          - listitem:
            - strong: деревня Лопатино
            - text: Потеря связи со всеми внешними городами-рынками
            - button "Выбрать пункт"
          - listitem:
            - strong: деревня Макарово
            - text: Потеря связи со всеми внешними городами-рынками
            - button "Выбрать пункт"
          - listitem:
            - strong: село Хотилово
            - text: Потеря связи со всеми внешними городами-рынками
            - button "Выбрать пункт"
          - listitem:
            - strong: деревня Поддубки
            - text: Потеря связи со всеми внешними городами-рынками
            - button "Выбрать пункт"
          - listitem:
            - strong: деревня Полустово
            - text: Потеря связи со всеми внешними городами-рынками
            - button "Выбрать пункт"
          - listitem:
            - strong: деревня Воскресенское
            - text: Потеря связи со всеми внешними городами-рынками
            - button "Выбрать пункт"
          - listitem:
            - strong: деревня Голениха
            - text: Потеря связи со всеми внешними городами-рынками
            - button "Выбрать пункт"
          - listitem:
            - strong: деревня Смолино
            - text: Потеря связи со всеми внешними городами-рынками
            - button "Выбрать пункт"
        - button "Назад" [disabled]
        - button "Далее"
      - region "Сценарий на графе":
        - group "Тип изменения":
          - text: Тип изменения
          - radio "Изменить дорогу" [checked]
          - text: Изменить дорогу
          - radio "Новая связь"
          - text: Новая связь
        - switch "Оценить экономический эффект"
        - text: Оценить экономический эффект
        - switch "Дорожный граф" [checked]
        - text: Дорожный граф
        - paragraph: Единый снимок data-20261107. База включает дороги и магистральные ЖД и авиасвязи. Лето и зима добавляют местные сезонные связи. Сезонных ограничений дорог в этом снимке нет.
        - paragraph: "Оранжевые линии: дорожный граф. Синяя линия: граница региона. Фиолетовый пунктир: предлагаемая связь. Серые дороги: фоновая карта OSM, которая может отличаться от снимка графа."
        - paragraph: "Новую связь можно задать в чате: назовите два места и время проезда. Агент найдёт узлы графа и запустит быстрый сценарий добавления."
        - paragraph: "На экране 79 433 отрезков, 193 802 направленных рёбер. Детализация: магистральные дороги. Дороги выбранных классов показаны целиком в этом окне."
        - 'heading "Выбранные дороги: 0" [level=2]'
        - paragraph: Приблизьте карту и нажмите на линию или выберите дорогу из списка. Изменится весь объект OSM, включая участки за пределами экрана. Линии соединяют узлы графа и не повторяют все изгибы дороги.
        - button "Выбрать Vaalimaanväylä (324839659)"
        - button "Выбрать Vaalimaanväylä (324843661)"
        - button "Выбрать Vaalimaanväylä (324843662)"
        - button "Выбрать Lappeenrannantie (324845441)"
        - button "Выбрать 324847509 (324847509)"
        - button "Выбрать Vaalimaanväylä (511768497)"
        - button "Выбрать 564410482 (564410482)"
        - button "Выбрать Lappeenrannantie (564410483)"
        - button "Выбрать 564410669 (564410669)"
        - button "Выбрать Vaalimaanväylä (565104860)"
        - button "Выбрать Vaalimaanväylä (565104861)"
        - button "Выбрать Vaalimaanväylä (565104862)"
        - text: Сеть расчёта
        - combobox "Сеть расчёта": Базовая сеть
        - group "Как изменить дорогу":
          - text: Как изменить дорогу
          - radio "Множитель скорости" [checked]
          - text: Множитель скорости
          - radio "Полосы и покрытие"
          - text: Полосы и покрытие
        - text: Множитель скорости выбранных дорог
        - textbox "Множитель скорости выбранных дорог": "1.2"
        - paragraph: "1,2: скорость выше на 20%. 1: контроль без изменений. 0: закрыть дороги. Время меняется обратно пропорционально скорости."
        - region "Изменения транспортных связей":
          - heading "Изменения транспортных связей" [level=2]
          - paragraph: Межгородские ж/д и авиасвязи соединяют 180 городов-рынков, время указано в пути; модель добавляет пересадку 1 ч для поезда и 2,5 ч для самолёта. Местные сезонные связи есть только в летней и зимней сети.
          - group "Сеть связей":
            - text: Сеть связей
            - radio "Межгородские ж/д и авиа" [checked]
            - text: Межгородские ж/д и авиа
            - radio "Местные сезонные"
            - text: Местные сезонные
          - text: Город, населённый пункт или регион
          - textbox "Город, населённый пункт или регион"
          - button "Показать связи" [disabled]
          - group "Добавить связь":
            - text: Добавить связь Вид связи
            - combobox "Вид связи": Поезд
            - text: Город отправления
            - textbox "Город отправления"
            - text: Город назначения
            - textbox "Город назначения"
            - text: Время в пути, часы
            - textbox "Время в пути, часы"
            - button "Добавить в сценарий"
        - paragraph: Выберите регион на карте для оценки индекса жителей.
        - button "Пересчитать индекс" [disabled]
        - text: История расчётов по регионам
        - combobox "История расчётов по регионам": Ставропольский край
        - heading "Ставропольский край" [level=2]
        - paragraph: "Базовая сеть, дорог в расчёте: 358"
        - button "Изменяемые участки"
        - text: До изменений 99,1514 После изменений 96,6067 Изменение индекса -2,5447
        - paragraph: "Население: 2 907 593. Населённых пунктов: 760. Рёбер сценария: 726. Время: 0,542 с. Нормировка базы сохранена."
    - button "Изменить размер чата"
  - button "Закрыть чат" [expanded]
- region "Уведомления":
  - list
```

# Test source

```ts
  1  | import { readFileSync } from "node:fs"
  2  | import AxeBuilder from "@axe-core/playwright"
  3  | import { expect, test } from "@playwright/test"
  4  | import type { StressRouteComparison } from "../src/shared/api/road-stress"
  5  | import s from "../src/shared/i18n/locales/ru/stress.json" with { type: "json" }
  6  | 
  7  | test("national stress workspace is keyboard accessible", async ({ page }, info) => {
  8  |   test.setTimeout(120_000)
  9  |   const errors: string[] = []
  10 |   page.on("pageerror", (error) => errors.push(error.message))
  11 |   await page.goto("/?panel=scenario")
  12 |   await expect(page.getByRole("heading", { name: s.title, exact: true })).toBeVisible({
  13 |     timeout: 60_000,
  14 |   })
  15 |   await expect(page.getByText(s.select, { exact: true })).toBeVisible()
  16 |   await expect
  17 |     .poll(async () => Number(await page.locator("[data-map-surface]").getAttribute("data-zoom")), {
  18 |       timeout: 90_000,
  19 |     })
  20 |     .toBeGreaterThan(0)
  21 |   await page.screenshot({ path: info.outputPath("stress-workspace-1440.png") })
  22 |   const result = await new AxeBuilder({ page }).include("main").analyze()
  23 |   expect(result.violations).toEqual([])
  24 |   expect(errors).toEqual([])
  25 | })
  26 | 
  27 | test("saved national result survives reload and opens its map", async ({ page, request }, info) => {
  28 |   test.setTimeout(120_000)
  29 |   const id = process.env.STRESS_JOB_ID
  30 |   if (!id) throw new Error("Prepare a completed real national stress test and set STRESS_JOB_ID")
  31 |   const response = await request.get(`/api/v1/road-stress-tests/${id}`)
  32 |   expect(response.ok()).toBeTruthy()
  33 |   expect((await response.json()).status).toBe("completed")
  34 |   await page.goto(`/?panel=scenario&stress=${id}`)
  35 |   await expect(page.getByRole("button", { name: s.overview, exact: true })).toBeVisible()
  36 |   await page.getByRole("button", { name: s.overview, exact: true }).click()
  37 |   await page.reload()
  38 |   await expect(page.getByRole("button", { name: s.overview, exact: true })).toBeVisible()
  39 |   await expect
  40 |     .poll(async () => Number(await page.locator("[data-map-surface]").getAttribute("data-zoom")), {
  41 |       timeout: 90_000,
  42 |     })
  43 |     .toBeGreaterThan(0)
  44 |   await page.getByRole("button", { name: s.overview, exact: true }).click()
  45 |   await expect(page.locator("[data-stress-job]")).toHaveAttribute("data-stress-job", id)
  46 |   await expect
  47 |     .poll(
  48 |       async () =>
  49 |         Number(await page.locator("[data-stress-closed]").getAttribute("data-stress-closed")),
  50 |       { timeout: 60_000 },
  51 |     )
  52 |     .toBeGreaterThan(0)
  53 |   await page.setViewportSize({ width: 1920, height: 1080 })
  54 |   await page.screenshot({ path: info.outputPath("stress-result-1920.png") })
  55 | })
  56 | 
  57 | test("real detour form renders both paths and keeps the closed roads", async ({ page }, info) => {
  58 |   test.setTimeout(240_000)
  59 |   const id = process.env.STRESS_JOB_ID
  60 |   if (!id) throw new Error("Set STRESS_JOB_ID to the completed M-10 scenario")
  61 |   const route = JSON.parse(
  62 |     readFileSync(new URL("../../work/road-stress/route-validation.json", import.meta.url), "utf8"),
  63 |   ) as StressRouteComparison
  64 |   await page.goto(`/?panel=scenario&stress=${id}`)
  65 |   await page.getByRole("button", { name: s.route, exact: true }).click()
  66 |   await page
  67 |     .getByRole("combobox", { name: s.origin, exact: true })
  68 |     .fill(route.origin.name.replace(/^.*? /, ""))
  69 |   await page.getByRole("option").filter({ hasText: route.origin.name }).first().click()
  70 |   await page
  71 |     .getByRole("combobox", { name: s.destination, exact: true })
  72 |     .fill(route.destination.name.replace(/^.*? /, ""))
  73 |   await page.getByRole("option").filter({ hasText: route.destination.name }).first().click()
  74 |   const response = page.waitForResponse(
  75 |     (r) => r.url().includes(`/${id}/routes`) && r.request().method() === "POST",
  76 |     { timeout: 180_000 },
  77 |   )
  78 |   await page.getByRole("button", { name: s.compare, exact: true }).click()
  79 |   expect((await response).ok()).toBeTruthy()
> 80 |   await expect(page.getByText(s.before, { exact: true })).toBeVisible()
     |                                                           ^ Error: expect(locator).toBeVisible() failed
  81 |   await expect(page.getByText(s.after, { exact: true })).toBeVisible()
  82 |   await expect(page.locator("[data-stress-job]")).toHaveAttribute("data-stress-job", id)
  83 |   await expect
  84 |     .poll(async () =>
  85 |       Number(await page.locator("[data-stress-closed]").getAttribute("data-stress-closed")),
  86 |     )
  87 |     .toBeGreaterThan(0)
  88 |   await page.screenshot({ path: info.outputPath("stress-detour-1440.png") })
  89 | })
  90 | 
```