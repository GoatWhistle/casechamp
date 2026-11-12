# Первичные региональные основания N05–N08: новая партия

Проверено 12.11.2026. Статус `published_edition_verified` относится к прочитанной официальной публикации. Полнота дальнейших изменений и текущая юридическая сила отдельно не доказаны; `currentnessStatus=unconfirmed`.

## Ненецкий автономный округ

[Официальный объединённый PDF](https://dizog.adm-nao.ru/media/uploads/userfiles/2026/09/28/%D0%A0%D0%9D%D0%93%D0%9F_%D1%81_%D0%B2%D0%BD.%D0%B8%D0%B7%D0%BC..pdf), ссылка из [раздела действующего департамента](https://dizog.adm-nao.ru/obshaya-informaciya/informaciya-o-deyatelnosti/komitet-gradostroitelnoj-deyatelnosti/normativy-gradostroitelnogo-proektirovaniya/). Первая страница — приказ от 10.12.2025 №19, изменяющий №4 от 04.04.2024 (с поправкой №5 от 16.04.2024); не путать дату папки 2026/09/28 с датой акта. Пункт 1 подпункт 3 дополняет нормы пунктом 11, таблица на с.2:

| Индекс/объект | Территория | Исходное значение | Режим |
|---|---|---|---|
| N07, библиотеки без уточнения типа | городской округ | 30–40 мин | транспортная доступность |
| тот же объект | городское поселение | 15–30 мин | шаговая/транспортная доступность |
| тот же объект | сельское поселение | 15–30 мин | шаговая/транспортная доступность |

Обе страницы просмотрены визуально. Это интервалы; ни 30, ни 40 мин нельзя выдавать за единственный универсальный порог. Запись через косую черту не уточняет, требуется ли совмещение режимов или выбор; автомобильная модель не разрешает эту неоднозначность. Для внедрения нужен явный способ обработки диапазонов и профиль библиотеки; до этого строки пригодны как условные нормативные основания. Число 36 в соседнем столбце — обеспеченность, не время пути. Положительные N05/N06/N08 в этом PDF не найдены; отсутствие найденной строки не означает `not_regulated`.

```json
{
  "metadata": {
    "regionCode": "83",
    "actDate": "2024-04-04",
    "actNumber": "4",
    "actAuthority": "Департамент строительства, жилищно-коммунального хозяйства, энергетики и транспорта Ненецкого автономного округа",
    "editionDate": "2025-12-10",
    "editionActNumber": "19",
    "sourceUrl": "https://dizog.adm-nao.ru/media/uploads/userfiles/2026/09/28/%D0%A0%D0%9D%D0%93%D0%9F_%D1%81_%D0%B2%D0%BD.%D0%B8%D0%B7%D0%BC..pdf",
    "verificationStatus": "published_edition_verified",
    "currentnessStatus": "unconfirmed",
    "verifiedAt": "2026-11-12",
    "planningNorm": true
  },
  "rows": [
    {
      "indexId": "N07",
      "facilityProfile": "library_type_not_specified",
      "metric": "transport_travel_time",
      "transportMode": "unspecified",
      "unit": "min",
      "thresholdMin": 30,
      "thresholdMax": 40,
      "thresholdRepresentation": "source_interval_not_single_cutoff",
      "scope": {
        "municipalityType": "urban_okrug"
      },
      "clause": "п.1 подп.3 поправки №19; п.11 НГП",
      "table": "п.11, строка «Библиотеки»",
      "pdfPage": 2,
      "printedPage": 2,
      "requiresLocalSelection": true
    },
    {
      "indexId": "N07",
      "facilityProfile": "library_type_not_specified",
      "metric": "pedestrian_or_transport_travel_time",
      "transportMode": "source_alternative_not_resolved",
      "unit": "min",
      "thresholdMin": 15,
      "thresholdMax": 30,
      "thresholdRepresentation": "source_interval_not_single_cutoff",
      "scope": {
        "municipalityType": "urban_settlement"
      },
      "clause": "п.1 подп.3 поправки №19; п.11 НГП",
      "table": "п.11, строка «Библиотеки»",
      "pdfPage": 2,
      "printedPage": 2,
      "requiresLocalSelection": true
    },
    {
      "indexId": "N07",
      "facilityProfile": "library_type_not_specified",
      "metric": "pedestrian_or_transport_travel_time",
      "transportMode": "source_alternative_not_resolved",
      "unit": "min",
      "thresholdMin": 15,
      "thresholdMax": 30,
      "thresholdRepresentation": "source_interval_not_single_cutoff",
      "scope": {
        "municipalityType": "rural_settlement"
      },
      "clause": "п.1 подп.3 поправки №19; п.11 НГП",
      "table": "п.11, строка «Библиотеки»",
      "pdfPage": 2,
      "printedPage": 2,
      "requiresLocalSelection": true
    }
  ]
}
```

## Воронежская область

[Официальная публикация 3601201710300002](http://publication.pravo.gov.ru/Document/View/3601201710300002), приказ управления архитектуры и градостроительства области от 09.10.2017 №45-01-04/115. Прочитана исходная публикация 2017 года, 82 страницы; последующие изменения не проверены. П.1 приказа утверждает приложение. Подраздел 1.3.9 приложения, ненумерованная таблица, строка 1.2 «Муниципальные библиотеки», печатные с.39–40 / PDF 41–42:

| Индекс/объект | Юридический тип территории | Транспортная доступность, исходный интервал |
|---|---|---|
| N07, муниципальные библиотеки | городской округ | 30–40 мин |
| тот же профиль | муниципальный район | 30–60 мин |
| тот же профиль | городское поселение | 15–30 мин |
| тот же профиль | сельское поселение | 15–30 мин |

Таблица охватывает межпоселенческие общедоступные/детские библиотеки, общедоступные библиотеки с детским отделением, общедоступные/детские библиотеки городского округа и филиалы общедоступных библиотек. Режим обозначен как транспортный без указания автомобиля или общественного транспорта. Табличные интервалы не сводятся к единому числу без дополнительного правила выбора. Тип МО из исходной редакции следует сопоставить с современным юридическим статусом.

Строка 1.1 задаёт иной профиль — государственные библиотеки регионального значения: 1 час для жителей Воронежа, 1 день для остальных муниципальных образований; не переносить на обычную муниципальную библиотеку. Положительные N05/N06/N08 в полном OCR и визуально просмотренной части не найдены; отсутствие найденной строки не доказывает отсутствия иных актов. Оба листа с N07 просмотрены визуально.

```json
{
  "metadata": {
    "regionCode": "36",
    "actDate": "2017-10-09",
    "actNumber": "45-01-04/115",
    "actAuthority": "Управление архитектуры и градостроительства Воронежской области",
    "editionDate": "2017-10-09",
    "sourceUrl": "http://publication.pravo.gov.ru/Document/View/3601201710300002",
    "sourcePdfUrl": "http://publication.pravo.gov.ru/file/pdf?eoNumber=3601201710300002",
    "verifiedAt": "2026-11-12",
    "verificationStatus": "published_edition_verified",
    "currentnessStatus": "unconfirmed",
    "planningNorm": true
  },
  "rows": [
    {
      "indexId": "N07",
      "facilityProfile": "municipal_public_library_or_branch",
      "metric": "transport_travel_time",
      "transportMode": "unspecified",
      "unit": "min",
      "thresholdMin": 30,
      "thresholdMax": 40,
      "thresholdRepresentation": "source_interval_not_single_cutoff",
      "requiresLocalSelection": true,
      "scope": {
        "municipalityType": "urban_okrug"
      },
      "clause": "1.3.9",
      "table": "unnumbered",
      "tableRow": "1.2",
      "printedPages": [
        39,
        40
      ],
      "pdfPages": [
        41,
        42
      ]
    },
    {
      "indexId": "N07",
      "facilityProfile": "municipal_public_library_or_branch",
      "metric": "transport_travel_time",
      "transportMode": "unspecified",
      "unit": "min",
      "thresholdMin": 30,
      "thresholdMax": 60,
      "thresholdRepresentation": "source_interval_not_single_cutoff",
      "requiresLocalSelection": true,
      "scope": {
        "municipalityType": "municipal_district"
      },
      "clause": "1.3.9",
      "table": "unnumbered",
      "tableRow": "1.2",
      "printedPages": [
        39,
        40
      ],
      "pdfPages": [
        41,
        42
      ]
    },
    {
      "indexId": "N07",
      "facilityProfile": "municipal_public_library_or_branch",
      "metric": "transport_travel_time",
      "transportMode": "unspecified",
      "unit": "min",
      "thresholdMin": 15,
      "thresholdMax": 30,
      "thresholdRepresentation": "source_interval_not_single_cutoff",
      "requiresLocalSelection": true,
      "scope": {
        "municipalityType": "urban_settlement"
      },
      "clause": "1.3.9",
      "table": "unnumbered",
      "tableRow": "1.2",
      "printedPages": [
        39,
        40
      ],
      "pdfPages": [
        41,
        42
      ]
    },
    {
      "indexId": "N07",
      "facilityProfile": "municipal_public_library_or_branch",
      "metric": "transport_travel_time",
      "transportMode": "unspecified",
      "unit": "min",
      "thresholdMin": 15,
      "thresholdMax": 30,
      "thresholdRepresentation": "source_interval_not_single_cutoff",
      "requiresLocalSelection": true,
      "scope": {
        "municipalityType": "rural_settlement"
      },
      "clause": "1.3.9",
      "table": "unnumbered",
      "tableRow": "1.2",
      "printedPages": [
        39,
        40
      ],
      "pdfPages": [
        41,
        42
      ]
    }
  ]
}
```

## Белгородская область

[Официальная публикация 3100201604290012](http://publication.pravo.gov.ru/Document/View/3100201604290012), постановление правительства области от 25.04.2016 №100-пп, 69 страниц. Исходная опубликованная редакция 2016 года, не текущая сводная редакция. На с.8 / PDF 8 таблица 2 «Объекты регионального значения», строка 2 «Автовокзалы, автостанции»: максимальный уровень территориальной доступности прямо **не нормируется**. Соседняя единица обеспеченности на городской округ/муниципальный район — не порог пути. Лист просмотрен визуально. Это scoped отрицательное нормативное основание, не утверждение об отсутствии транспортных требований в других актах или последующих редакциях.

```json
{
  "metadata": {
    "regionCode": "31",
    "actDate": "2016-04-25",
    "actNumber": "100-пп",
    "actAuthority": "Правительство Белгородской области",
    "editionDate": "2016-04-25",
    "sourceUrl": "http://publication.pravo.gov.ru/Document/View/3100201604290012",
    "sourcePdfUrl": "http://publication.pravo.gov.ru/file/pdf?eoNumber=3100201604290012",
    "verifiedAt": "2026-11-12",
    "verificationStatus": "published_edition_verified",
    "currentnessStatus": "unconfirmed",
    "planningNorm": true
  },
  "rows": [
    {
      "indexId": "N08",
      "facilityProfile": "regional_bus_terminal_or_bus_station",
      "threshold": null,
      "status": "not_normed_in_verified_edition",
      "regulation": "not_regulated",
      "scope": {
        "municipalityTypes": [
          "urban_okrug",
          "municipal_district"
        ]
      },
      "table": "2",
      "tableRow": 2,
      "printedPage": 8,
      "pdfPage": 8
    }
  ]
}
```

Положительные N05/N06/N07 в полном тексте этой исходной публикации не найдены. Нельзя превращать это наблюдение в `not_regulated` по всему субъекту. Новые редакции, включая известную по поисковым указателям поправку 2023 года №698-пп, в рамках этой партии не прочитаны; отрицательная строка 2016года требует особенно явного обозначения редакции.

## Вологодская область: ограничение первоисточника

[Официальная карточка №338 от 11.04.2016](https://vologda-oblast.ru/dokumenty/zakony_i_postanovleniya/postanovleniya_pravitelstva/615619/) ссылается на [DOC](https://vologda-oblast.ru/upload/iblock/d0d/117542.doc). Файл скачан и прочитан: содержит постановляющую часть без приложения с таблицами. Пороги из него не выводились. Вторичные правовые базы не использованы для подтверждения числа.

## Копии и проверка

Первичные публикации Воронежа/Белгорода найдены через [официально документированный API](http://publication.pravo.gov.ru/help), запросами `/api/Documents` с `Block=region36|region31`, точным `Number` и `PageSize=200`. Даты, номера, UUID и размеры подтверждены метаданными ответа. PDF полностью скачаны, страницы распознаны локально; строки выше проверены по изображению, не только OCR.

| `.local/research/` | SHA256 |
|---|---|
| `nao-rngp.pdf` | `8b56cb5902c08233a5ea0a08537ed974d45af14abfbdd1f7371adde60d9463ee` |
| `voronezh-115.pdf` | `424ef00907ae5a98987ba95f17cf9d107792c98dd0dca683fe9fa8ce00d24e8e` |
| `belgorod-100.pdf` | `5040412c0e6e47dcdefcbc6f69201e819fb234ed01b00161204a2f8d26136efc` |

Результат: 2 субъекта с положительными интервальными N07 и 1 субъект с явным scoped `not_normed` для N08 в опубликованной редакции. Однозначных новых N05/N06 и автомобильных минут эта партия не дала. Основной код не изменялся.
