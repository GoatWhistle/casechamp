# Следующие первичные региональные основания N05–N08

Дата проверки: 12.11.2026. Проверенная опубликованная редакция не означает проверенную действующую редакцию. Везде `comparison <=`; классификацию территории применять до расчёта, не выбирать единый порог по субъекту.

## Свердловская область

[Официальный акт №435-П от 01.08.2023](https://www.pravo.gov66.ru/media/pravo/%D0%9F%D0%A0%D0%98%D0%9A%D0%90%D0%97%D0%BE%D1%8201.08.2023435-%D0%9F.pdf). Пункт1 приказа, утверждающий НГП, вступает в силу 01.02.2024 (п.4). Полный PDF 190 страниц скачан; таблицы 25, 40, 4 просмотрены визуально. Последующая цепочка изменений не проверена. Раздел «Правила и область применения основной части» распространяет нормы на подготовку/изменение территориальных документов области и муниципалитетов, ПЗЗ и документации по планировке. Юридический тип муниципалитета и группа из редакции 2023 года требуют сопоставления с актуальным административным устройством; автоматически заменять «городской округ» на «муниципальный округ» нельзя.

| Индекс | Профиль/территория | Режим и порог | Основание: печатная/PDF-страница |
|---|---|---|---|
| N05 | МФЦ, субъект | транспорт, 45 мин; вид транспорта не назван | п.1.13, табл.25:55/57 |
| N07 | Общедоступная муниципальная библиотека/филиал; городской округ | транспорт, 40 мин | п.2.7, табл.40, строка1:72/74 |
| N07 | Муниципальный район | транспорт, 60 мин | там же |
| N07 | Городское/сельское поселение | транспорт, 30 мин; отдельно пешком 30 мин | там же; сельский пеший профиль — филиал |
| N08 | Автовокзал/автостанция, сельская местность | личное авто:А40/Б60/В90мин; общественный транспорт:А60/Б80/В110мин | п.1.1, табл.4:14–15/16–17 |

Для N08 городская местность прямо не нормируется. Группы ТПО задаёт приложение Ж, табл. Ж1, с.96–98 (PDF 98–100); это классификация муниципалитетов, не плотность/расстояние, выведенные моделью. Проверенные примеры: Арамильский ГО=А; Артёмовский ГО=Б; Белоярский ГО=В. Автовокзал: пассажирооборот>1000/сутки; автостанция:<1000/сутки, ровно 1000 отдельно не разрешено текстом. Ссылки на федеральные правила размещения не меняют маршрут жильё→объект. N06 положительная строка не найдена; не превращать отсутствие найденного основания в `not_regulated`.

```json
{
  "metadata": {
    "regionCode": "66",
    "actDate": "2023-08-01",
    "actNumber": "435-П",
    "actAuthority": "Министерство строительства и развития инфраструктуры Свердловской области",
    "editionDate": "2023-08-01",
    "effectiveFrom": "2024-02-01",
    "sourceUrl": "https://www.pravo.gov66.ru/media/pravo/%D0%9F%D0%A0%D0%98%D0%9A%D0%90%D0%97%D0%BE%D1%8201.08.2023435-%D0%9F.pdf",
    "verificationStatus": "published_edition_verified",
    "currentnessStatus": "unconfirmed",
    "verifiedAt": "2026-11-12",
    "planningNorm": true
  },
  "rows": [
    {
      "indexId": "N05",
      "facilityProfile": "mfc",
      "metric": "transport_travel_time",
      "transportMode": "unspecified",
      "unit": "min",
      "threshold": 45,
      "scope": "region",
      "clause": "1.13",
      "table": "25",
      "printedPage": 55,
      "pdfPage": 57
    },
    {
      "indexId": "N07",
      "facilityProfile": "municipal_public_library_or_branch",
      "metric": "transport_travel_time",
      "transportMode": "unspecified",
      "unit": "min",
      "threshold": 40,
      "scope": {
        "municipalityType": "urban_okrug"
      },
      "clause": "2.7",
      "table": "40",
      "tableRow": 1,
      "printedPage": 72,
      "pdfPage": 74
    },
    {
      "indexId": "N07",
      "facilityProfile": "municipal_public_library_or_branch",
      "metric": "transport_travel_time",
      "transportMode": "unspecified",
      "unit": "min",
      "threshold": 60,
      "scope": {
        "municipalityType": "municipal_district"
      },
      "clause": "2.7",
      "table": "40",
      "tableRow": 1,
      "printedPage": 72,
      "pdfPage": 74
    },
    {
      "indexId": "N07",
      "facilityProfile": "municipal_public_library_or_branch",
      "metric": "transport_travel_time",
      "transportMode": "unspecified",
      "unit": "min",
      "threshold": 30,
      "scope": {
        "municipalityType": "urban_settlement"
      },
      "clause": "2.7",
      "table": "40",
      "tableRow": 1,
      "printedPage": 72,
      "pdfPage": 74
    },
    {
      "indexId": "N07",
      "facilityProfile": "municipal_public_library_or_branch",
      "metric": "transport_travel_time",
      "transportMode": "unspecified",
      "unit": "min",
      "threshold": 30,
      "scope": {
        "municipalityType": "rural_settlement"
      },
      "clause": "2.7",
      "table": "40",
      "tableRow": 1,
      "printedPage": 72,
      "pdfPage": 74
    },
    {
      "indexId": "N07",
      "facilityProfile": "municipal_public_library_or_branch",
      "metric": "pedestrian_travel_time",
      "unit": "min",
      "threshold": 30,
      "scope": {
        "municipalityType": "urban_settlement"
      },
      "clause": "2.7",
      "table": "40",
      "tableRow": 1,
      "printedPage": 72,
      "pdfPage": 74
    },
    {
      "indexId": "N07",
      "facilityProfile": "municipal_library_branch",
      "metric": "pedestrian_travel_time",
      "unit": "min",
      "threshold": 30,
      "scope": {
        "municipalityType": "rural_settlement"
      },
      "clause": "2.7",
      "table": "40",
      "tableRow": 1,
      "printedPage": 72,
      "pdfPage": 74
    },
    {
      "indexId": "N08",
      "facilityProfile": "bus_terminal_or_bus_station",
      "metric": "car_travel_time",
      "unit": "min",
      "threshold": 40,
      "scope": {
        "settlementType": "rural",
        "municipalityTpoGroup": "A",
        "groupSource": "Приложение Ж, табл. Ж1, с.96–98",
        "sourceGroupLabel": "А"
      },
      "clause": "1.1",
      "table": "4",
      "printedPages": [
        14,
        15
      ],
      "pdfPages": [
        16,
        17
      ],
      "profileRules": {
        "bus_terminal": "passenger_turnover_gt_1000_per_day",
        "bus_station": "passenger_turnover_lt_1000_per_day"
      }
    },
    {
      "indexId": "N08",
      "facilityProfile": "bus_terminal_or_bus_station",
      "metric": "car_travel_time",
      "unit": "min",
      "threshold": 60,
      "scope": {
        "settlementType": "rural",
        "municipalityTpoGroup": "B",
        "groupSource": "Приложение Ж, табл. Ж1, с.96–98",
        "sourceGroupLabel": "Б"
      },
      "clause": "1.1",
      "table": "4",
      "printedPages": [
        14,
        15
      ],
      "pdfPages": [
        16,
        17
      ],
      "profileRules": {
        "bus_terminal": "passenger_turnover_gt_1000_per_day",
        "bus_station": "passenger_turnover_lt_1000_per_day"
      }
    },
    {
      "indexId": "N08",
      "facilityProfile": "bus_terminal_or_bus_station",
      "metric": "car_travel_time",
      "unit": "min",
      "threshold": 90,
      "scope": {
        "settlementType": "rural",
        "municipalityTpoGroup": "C",
        "groupSource": "Приложение Ж, табл. Ж1, с.96–98",
        "sourceGroupLabel": "В"
      },
      "clause": "1.1",
      "table": "4",
      "printedPages": [
        14,
        15
      ],
      "pdfPages": [
        16,
        17
      ],
      "profileRules": {
        "bus_terminal": "passenger_turnover_gt_1000_per_day",
        "bus_station": "passenger_turnover_lt_1000_per_day"
      }
    },
    {
      "indexId": "N08",
      "facilityProfile": "bus_terminal_or_bus_station",
      "metric": "public_transport_travel_time",
      "unit": "min",
      "threshold": 60,
      "scope": {
        "settlementType": "rural",
        "municipalityTpoGroup": "A",
        "groupSource": "Приложение Ж, табл. Ж1, с.96–98",
        "sourceGroupLabel": "А"
      },
      "clause": "1.1",
      "table": "4",
      "printedPages": [
        14,
        15
      ],
      "pdfPages": [
        16,
        17
      ],
      "profileRules": {
        "bus_terminal": "passenger_turnover_gt_1000_per_day",
        "bus_station": "passenger_turnover_lt_1000_per_day"
      }
    },
    {
      "indexId": "N08",
      "facilityProfile": "bus_terminal_or_bus_station",
      "metric": "public_transport_travel_time",
      "unit": "min",
      "threshold": 80,
      "scope": {
        "settlementType": "rural",
        "municipalityTpoGroup": "B",
        "groupSource": "Приложение Ж, табл. Ж1, с.96–98",
        "sourceGroupLabel": "Б"
      },
      "clause": "1.1",
      "table": "4",
      "printedPages": [
        14,
        15
      ],
      "pdfPages": [
        16,
        17
      ],
      "profileRules": {
        "bus_terminal": "passenger_turnover_gt_1000_per_day",
        "bus_station": "passenger_turnover_lt_1000_per_day"
      }
    },
    {
      "indexId": "N08",
      "facilityProfile": "bus_terminal_or_bus_station",
      "metric": "public_transport_travel_time",
      "unit": "min",
      "threshold": 110,
      "scope": {
        "settlementType": "rural",
        "municipalityTpoGroup": "C",
        "groupSource": "Приложение Ж, табл. Ж1, с.96–98",
        "sourceGroupLabel": "В"
      },
      "clause": "1.1",
      "table": "4",
      "printedPages": [
        14,
        15
      ],
      "pdfPages": [
        16,
        17
      ],
      "profileRules": {
        "bus_terminal": "passenger_turnover_gt_1000_per_day",
        "bus_station": "passenger_turnover_lt_1000_per_day"
      }
    }
  ]
}
```

## Татарстан

[Официальная министерская копия №1071 от 27.12.2013, редакция 15.01.2024](https://minstroy.tatarstan.ru/file/minstroy/File/%D0%9F%D0%BE%D1%81%D1%82%D0%B0%D0%BD%D0%BE%D0%B2%D0%BB%D0%B5%D0%BD%D0%B8%D0%B5%20%D0%9A%D0%9C%20%D0%A0%D0%A2%20%D0%BE%D1%82%2027%20%D0%B4%D0%B5%D0%BA%D0%B0%D0%B1%D1%80%D1%8F%202013%20%D0%B3%20N%201071%20%D0%9E%D0%B1%20%D1%83%D1%82%D0%B2%D0%B5%D1%80%D0%B6%D0%B4%D0%B5%D0%BD%D0%B8%D0%B8%20%D1%80%D0%B5%D1%81%D0%BF%D1%83%D0%B1%D0%BB%D0%B8%D0%BA%D0%B0%D0%BD%D1%81%D0%BA%D0%B8%D1%85%20%D0%BD%D0%BE%D1%80%D0%BC%D0%B0%D1%82%D0%B8%D0%B2%D0%BE%D0%B2%281%29.pdf),178 страниц; сохранена системой 18.01.2024. П.1.1, табл.1, строки 5–6, с.8 просмотрены визуально: автовокзалы/автостанции,35/55/90км по группам ТПП А/Б/В. Исходная точка — наиболее удалённый населённый пункт муниципалитета. Это предел по муниципалитету, не норматив времени и не процент жителей. Метод измерения расстояния текстом строки не определён.

Группировка — приложение N1, с.160–163, территориально-пространственное положение относительно центров агломераций; не путать с ТПО приложения N2. Проверенные примеры приложения: Арский район=А, Алексеевский район=Б, Дрожжановский район=В. Фильтры и режим не позволяют напрямую применить существующую автомобильную матрицу времени.

Последующие официальные акты найдены и прочитаны: [№967 от 18.11.2025](https://pravo.tatarstan.ru/file/npa/2025-11/1717235/npa_1717236.pdf), [№504 от 23.04.2026](https://pravo.tatarstan.ru/file/npa/2026-04/1829045/npa_1829046.pdf). Они не меняют эту строку N08; полнота последующей цепочки не установлена. №504 заменяет таблицу 10 библиотек регионального значения: эти специализированные профили не подставлять вместо общедоступной муниципальной библиотеки N07. Для N05/N06 и муниципального N07 готовой положительной строки нет.

```json
{
  "metadata": {
    "regionCode": "16",
    "actDate": "2013-12-27",
    "actNumber": "1071",
    "actAuthority": "Кабинет Министров Республики Татарстан",
    "editionDate": "2024-01-15",
    "sourceUrl": "https://minstroy.tatarstan.ru/file/minstroy/File/%D0%9F%D0%BE%D1%81%D1%82%D0%B0%D0%BD%D0%BE%D0%B2%D0%BB%D0%B5%D0%BD%D0%B8%D0%B5%20%D0%9A%D0%9C%20%D0%A0%D0%A2%20%D0%BE%D1%82%2027%20%D0%B4%D0%B5%D0%BA%D0%B0%D0%B1%D1%80%D1%8F%202013%20%D0%B3%20N%201071%20%D0%9E%D0%B1%20%D1%83%D1%82%D0%B2%D0%B5%D1%80%D0%B6%D0%B4%D0%B5%D0%BD%D0%B8%D0%B8%20%D1%80%D0%B5%D1%81%D0%BF%D1%83%D0%B1%D0%BB%D0%B8%D0%BA%D0%B0%D0%BD%D1%81%D0%BA%D0%B8%D1%85%20%D0%BD%D0%BE%D1%80%D0%BC%D0%B0%D1%82%D0%B8%D0%B2%D0%BE%D0%B2%281%29.pdf",
    "verificationStatus": "published_edition_verified",
    "currentnessStatus": "unconfirmed",
    "verifiedAt": "2026-11-12",
    "planningNorm": true
  },
  "rows": [
    {
      "indexId": "N08",
      "facilityProfile": "bus_terminal_or_bus_station",
      "metric": "distance_from_most_remote_settlement",
      "distanceMethod": "not_specified",
      "unit": "km",
      "threshold": 35,
      "scope": {
        "municipalityTppGroup": "A",
        "groupSource": "Приложение N1, с.160–163",
        "sourceGroupLabel": "А"
      },
      "origin": "most_remote_settlement_of_municipality",
      "aggregation": "municipality_worst_settlement",
      "clause": "1.1",
      "table": "1",
      "tableRows": [
        5,
        6
      ],
      "printedPage": 8,
      "pdfPage": 8
    },
    {
      "indexId": "N08",
      "facilityProfile": "bus_terminal_or_bus_station",
      "metric": "distance_from_most_remote_settlement",
      "distanceMethod": "not_specified",
      "unit": "km",
      "threshold": 55,
      "scope": {
        "municipalityTppGroup": "B",
        "groupSource": "Приложение N1, с.160–163",
        "sourceGroupLabel": "Б"
      },
      "origin": "most_remote_settlement_of_municipality",
      "aggregation": "municipality_worst_settlement",
      "clause": "1.1",
      "table": "1",
      "tableRows": [
        5,
        6
      ],
      "printedPage": 8,
      "pdfPage": 8
    },
    {
      "indexId": "N08",
      "facilityProfile": "bus_terminal_or_bus_station",
      "metric": "distance_from_most_remote_settlement",
      "distanceMethod": "not_specified",
      "unit": "km",
      "threshold": 90,
      "scope": {
        "municipalityTppGroup": "C",
        "groupSource": "Приложение N1, с.160–163",
        "sourceGroupLabel": "В"
      },
      "origin": "most_remote_settlement_of_municipality",
      "aggregation": "municipality_worst_settlement",
      "clause": "1.1",
      "table": "1",
      "tableRows": [
        5,
        6
      ],
      "printedPage": 8,
      "pdfPage": 8
    }
  ]
}
```

## Самарская область

[Первичная публикация №235-п от 31.03.2026](http://publication.pravo.gov.ru/Document/View/6301202604020004), [полная официальная муниципальная копия](https://admpriboy.ru/kcfinder/upload/1008/files/new/3103-235-p-2.pdf), 189 страниц. Нормативная часть — сканы без текста: страницы 1–90 локально распознаны; все приведённые строки затем проверены визуально. Приказ отменяет №526-п/2014 (п.4). [Официальная поправка №621-п от 30.07.2026](http://publication.pravo.gov.ru/Document/View/6301202607310004), обе страницы, меняет только п.7 о вступлении в силу: теперь оно привязано к Закону области от 16.07.2026 №89-ГД. Точную дату вступления самого закона в этом проходе не проверяли; числовые таблицы поправка не меняет.

| Индекс | Профиль/область применения | Порог | Основание, печатная/PDF-страница |
|---|---|---|---|
| N08 | Автовокзал/автостанция регионального и межрегионального сообщения | 45 мин на транспорте | раздел I, подраздел 2, п.17, табл.1, строка 4: 6/8 |
| N05 | Приём/выдача документов МФЦ, МО от 1 тыс. жителей | доступность прямо не установлена | табл.9, строки 1–2: 29/31 |
| N07 | Межпоселенческая библиотека муниципального района | доступность прямо не установлена | табл.13, строка 1: 35/37 |
| N07 | Общедоступная библиотека городского округа | доступность прямо не установлена | табл.22, строка 1: 66/68 |

П.6 общих положений определяет транспортную доступность как движение с использованием транспортных средств по улицам/дорогам общего пользования и другим транспортным объектам; вид транспорта в N08 отдельно не закреплён. П.1 требует применение при подготовке документов территориального планирования области/МО и документации по планировке территории; п.2 рекомендует при подготовке ПЗЗ. П.3 приказа до обновления местных НГП предписывает использование региональных пределов для местных объектов. Не расширять профиль N08 на любую остановку или заведомо только местный объект. N05/N07: отсутствие числа в проверенной строке не доказывает отсутствия иных требований в других актах. Для N05 таблица 9 явно описывает только муниципалитеты от 1 тыс. жителей, поэтому JSON сохраняет эту границу; у малых территорий и иных форм обслуживания отсутствие порога отдельно не доказано. Для N07 поселения отдельно не просмотрены полностью; `not_normed` по всему субъекту не выводится. N06 положительное основание не найдено.

```json
{
  "metadata": {
    "regionCode": "63",
    "actDate": "2026-03-31",
    "actNumber": "235-п",
    "actAuthority": "Министерство градостроительной политики Самарской области",
    "editionDate": "2026-03-31",
    "sourceUrl": "https://admpriboy.ru/kcfinder/upload/1008/files/new/3103-235-p-2.pdf",
    "publicationUrl": "http://publication.pravo.gov.ru/Document/View/6301202604020004",
    "verificationStatus": "published_edition_verified",
    "currentnessStatus": "unconfirmed",
    "verifiedAt": "2026-11-12",
    "planningNorm": true,
    "laterAmendmentsChecked": [
      {
        "actDate": "2026-07-30",
        "actNumber": "621-п",
        "affectsNumericRows": false,
        "sourceUrl": "http://publication.pravo.gov.ru/Document/View/6301202607310004"
      }
    ]
  },
  "rows": [
    {
      "indexId": "N08",
      "facilityProfile": "regional_or_interregional_bus_terminal_or_station",
      "metric": "transport_travel_time",
      "transportMode": "unspecified",
      "unit": "min",
      "threshold": 45,
      "comparison": "<=",
      "scope": "region",
      "clause": "Раздел I, подраздел 2, п.17",
      "table": "1",
      "tableRow": 4,
      "printedPage": 6,
      "pdfPage": 8
    },
    {
      "indexId": "N05",
      "facilityProfile": "mfc_receiving_window",
      "threshold": null,
      "status": "not_normed_in_verified_edition",
      "scope": {
        "municipalityPopulationMin": 1000
      },
      "table": "9",
      "tableRows": [
        1,
        2
      ],
      "printedPage": 29,
      "pdfPage": 31
    },
    {
      "indexId": "N07",
      "facilityProfile": "intersettlement_municipal_library",
      "threshold": null,
      "status": "not_normed_in_verified_edition",
      "scope": {
        "municipalityType": "municipal_district"
      },
      "table": "13",
      "tableRow": 1,
      "printedPage": 35,
      "pdfPage": 37
    },
    {
      "indexId": "N07",
      "facilityProfile": "municipal_public_library",
      "threshold": null,
      "status": "not_normed_in_verified_edition",
      "scope": {
        "municipalityType": "urban_okrug"
      },
      "table": "22",
      "tableRow": 1,
      "printedPage": 66,
      "pdfPage": 68
    }
  ]
}
```

## Локальные копии и воспроизводимость

| Копия в `.local/research/` | SHA256 |
|---|---|
| `sverdlovsk-complete.pdf` | `fa9a74460902e724f5079d0095a4458e20f7753734963dd752aa0f8fad050efd` |
| `tatarstan-1071.pdf` | `c7eb77e78dfd6c09b3a365f23b0071ba7bdaa656707c3f553af5b74b43f362cd` |
| `samara-complete.pdf` | `adadaa60309e57d9f6418228b4534dc1b1b92a44f09abd413cd7c89256c3ae37` |

Изменений основного кода, коммитов и публикации нет. Нормативные числа не являются измерением фактической доступности.
