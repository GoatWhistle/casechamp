# Первичные региональные основания N05–N08

Проверено 12.11.2026. В JSON ниже — подтверждённые значения опубликованной редакции, а не заключение о действующем праве на дату проверки.

## Подтверждено: Костромская область

[Официальная муниципальная публикация №344-а](https://volgorechensk.kostroma.gov.ru/upload/medialibrary/314/bg3woub6g8dahlrb9aixaucgkb1tes8e/344-%D0%B0.pdf), редакция 20.01.2025: п.2 постановления распространяет применение на градостроительную деятельность всей области. Пороги транспортные; часы переведены в минуты арифметически. Пешеходный радиус, дорожное расстояние и время ожидания ими не задаются.

| Индекс | Профиль | Порог | Основание, печатная страница |
|---|---|---|---|
| N05 | МФЦ | 90 мин | п.14, табл.8, с.29 |
| N06 | ЦЗН | 90 мин | п.14, табл.8, с.29 |
| N07 | Муниципальная общедоступная библиотека: городской/муниципальный округ | 40 мин | п.21, табл.15, строки 3–4, с.41 |
| N07 | Та же категория: муниципальный район | 60 мин | там же |
| N08 | Межмуниципальный автовокзал/автостанция | 90 мин | п.4, табл.1, с.5–6 |
| N08 | Региональный автовокзал | 240 мин | п.4, табл.1, с.5 |

Таблица 15 изменена актом 20.01.2025 №13-а. Категории муниципалитетов определяются юридическим статусом, не городской/сельской местностью. Региональные специализированные библиотеки таблицы 6 — другой профиль. Глава 7 запрещает местным нормам превышать региональные пределы доступности; местные акты могут быть строже. Для расчёта нужен действующий статус муниципалитета и подходящий объект. Список всех OSM-библиотек или остановок такой фильтр не заменяет.

Копия: `.local/research/kostroma-primary.pdf`,1 595 593 байта; SHA256 `bd62c77c71b7609cea9b4528b61177742e1e44054a4b09a73ba00b10af37bb77`. PDF содержит обложку: печатная страница 29 соответствует файлу 30. Полный текст извлечён через `pdftotext -layout`; таблицы 8, 15 и продолжение 1 просмотрены визуально. Самостоятельная цепочка последующих изменений не проверена.

## Предлагаемые структурированные строки

Метаданные наследуются каждой строкой. `municipalityTypes` обязательны для N07; без них нельзя выбирать единый порог по области. Профили N08 не объединять. `planningNorm` означает норматив планирования: результат сравнения — аналитический сигнал, не автоматическое юридическое заключение о нарушении существующим учреждением.

```json
{
  "metadata": {
    "regionCode": "44",
    "regionName": "Костромская область",
    "actType": "Постановление администрации Костромской области",
    "actDate": "2010-10-01",
    "actNumber": "344-а",
    "editionDate": "2025-01-20",
    "sourceUrl": "https://volgorechensk.kostroma.gov.ru/upload/medialibrary/314/bg3woub6g8dahlrb9aixaucgkb1tes8e/344-%D0%B0.pdf",
    "sourceSavedDate": "2025-04-22",
    "verifiedAt": "2026-11-12",
    "verificationStatus": "published_edition_verified",
    "currentnessStatus": "unconfirmed",
    "metric": "transport_travel_time",
    "unit": "min",
    "comparison": "<=",
    "territorialScope": "region",
    "planningNorm": true
  },
  "rows": [
    {
      "indexId": "N05",
      "facilityProfile": "mfc",
      "threshold": 90,
      "originalValue": 1.5,
      "originalUnit": "hour",
      "clause": "14",
      "table": "8",
      "printedPage": 29
    },
    {
      "indexId": "N06",
      "facilityProfile": "employment_centre",
      "threshold": 90,
      "originalValue": 1.5,
      "originalUnit": "hour",
      "clause": "14",
      "table": "8",
      "printedPage": 29
    },
    {
      "indexId": "N07",
      "facilityProfile": "municipal_public_library",
      "threshold": 40,
      "municipalityTypes": [
        "urban_okrug",
        "municipal_okrug"
      ],
      "clause": "21",
      "table": "15",
      "tableRows": [
        3
      ],
      "printedPage": 41
    },
    {
      "indexId": "N07",
      "facilityProfile": "municipal_public_library",
      "threshold": 60,
      "municipalityTypes": [
        "municipal_district"
      ],
      "clause": "21",
      "table": "15",
      "tableRows": [
        4
      ],
      "printedPage": 41
    },
    {
      "indexId": "N08",
      "facilityProfile": "intermunicipal_bus_station",
      "threshold": 90,
      "originalValue": 1.5,
      "originalUnit": "hour",
      "clause": "4",
      "table": "1",
      "printedPages": [
        5,
        6
      ]
    },
    {
      "indexId": "N08",
      "facilityProfile": "regional_bus_terminal",
      "threshold": 240,
      "originalValue": 4,
      "originalUnit": "hour",
      "clause": "4",
      "table": "1",
      "printedPage": 5
    }
  ]
}
```

## Подтверждено: Санкт-Петербург

[Официальная публикация №1357 от 19.12.2023](http://publication.pravo.gov.ru/Document/View/7800202312200008) полностью заменяет приложение к №257 от 11.04.2017 (п.1.2). Пункт 1.1.1 приложения задаёт область действия — население Санкт-Петербурга, объекты регионального значения. Пункт 2 акта исключает документацию по планировке территории, утверждённую до вступления изменения в силу. Это ограничивает юридические выводы по существующей застройке.

| Индекс | Показатель | Пункт приложения | Печатная страница / номер изображения портала |
|---|---|---|---|
| N05 | МФЦ: пешеходно-транспортная доступность ≤45 мин | 1.2.20 | 7 / 8 |
| N07 | Общедоступная библиотека: пешеходно-транспортная доступность ≤30 мин | 1.2.15 | 6 / 7 |
| N08 | Автовокзал: показатель доступности прямо не установлен | 1.2.2 | 3 / 4 |

Проверены исходные сканы [N05](http://publication.pravo.gov.ru/GetImage?documentId=c6b0392b-9fda-4d81-9fef-df9739ab3e50&pageNumber=8), [N07](http://publication.pravo.gov.ru/GetImage?documentId=c6b0392b-9fda-4d81-9fef-df9739ab3e50&pageNumber=7), [N08](http://publication.pravo.gov.ru/GetImage?documentId=c6b0392b-9fda-4d81-9fef-df9739ab3e50&pageNumber=4), [область действия](http://publication.pravo.gov.ru/GetImage?documentId=c6b0392b-9fda-4d81-9fef-df9739ab3e50&pageNumber=2) и [переходное положение](http://publication.pravo.gov.ru/GetImage?documentId=c6b0392b-9fda-4d81-9fef-df9739ab3e50&pageNumber=1). Файлы `.local/research/spb-page{1,2,4,7,8}.png`. HTTPS не отвечал, официальный HTTP сработал.

Пешеходно-транспортный режим нельзя автоматически оценивать автомобильной матрицей. N08 получает состояние `not_normed_in_verified_edition`, не нулевой порог. Для ЦЗН положительное основание не найдено; это не доказывает отсутствия нормы в других актах.

[Официальное последующее изменение №146 от 18.03.2026](http://publication.pravo.gov.ru/Document/View/7800202603230001), обе страницы, скачано и просмотрено: добавляет нормы стоянок СИМ (п.1.2.13, 2.2.13.5, 3.11), указанные N05/N07/N08 не меняет. Копия `.local/research/spb-146.pdf`. Это проверка конкретной поправки; полнота всей последующей цепочки не доказана, поэтому `currentnessStatus` остаётся `unconfirmed`.

```json
{
  "metadata": {
    "regionCode": "78",
    "regionName": "Санкт-Петербург",
    "actType": "Постановление Правительства Санкт-Петербурга",
    "actDate": "2017-04-11",
    "actNumber": "257",
    "editionDate": "2023-12-19",
    "editionActNumber": "1357",
    "sourceUrl": "http://publication.pravo.gov.ru/Document/View/7800202312200008",
    "verifiedAt": "2026-11-12",
    "verificationStatus": "published_edition_verified",
    "currentnessStatus": "unconfirmed",
    "territorialScope": "region",
    "metric": "pedestrian_transit_travel_time",
    "unit": "min",
    "comparison": "<=",
    "planningNorm": true,
    "laterAmendmentsChecked": [
      {
        "actDate": "2026-03-18",
        "actNumber": "146",
        "affectsTheseRows": false,
        "sourceUrl": "http://publication.pravo.gov.ru/Document/View/7800202603230001"
      }
    ]
  },
  "rows": [
    {
      "indexId": "N05",
      "facilityProfile": "mfc",
      "threshold": 45,
      "clause": "1.2.20",
      "printedPage": 7,
      "sourceImageNumber": 8
    },
    {
      "indexId": "N07",
      "facilityProfile": "public_library",
      "threshold": 30,
      "clause": "1.2.15",
      "printedPage": 6,
      "sourceImageNumber": 7
    }
  ]
}
```

## Московская область: в импорт не включать

- Московская область: [официальная карточка №713/30 от 17.08.2015](https://mosreg.ru/dokumenty/normotvorchestvo/prinyato-pravitelstvom/postanovlenie-pravitelstva-moskovskoy-oblasti-ot-17082015-71330-ob-utverzhdenii-normativov-gradostroitelnogo-proektirovaniya-moskovskoy-oblasti) ссылается на [исходный PDF](https://mosreg.ru/upload/iblock/b9d/713_30.pdf),40 588 587 байт. Веб-инструмент отказал из-за размера; curl вернул HTML. Исходная редакция 2015 года не подтверждает текущий порог. [Официальное изменение №1238-ПП от 25.09.2025](https://mosreg.ru/dokumenty/normotvorchestvo/prinyato-pravitelstvom/postanovleniya-pmo/postanovlenie-pravitelstva-moskovskoi-oblasti-ot-25092025-1238-pp-o-vnesenii-izmenenii-v-postanovlenie-pravitelstva-moskovskoi-oblasti-ot-17082015-71330-ob-utverzdenii-normativov-gradostroitelnogo-proektirovaniia-moskovskoi-oblasti) показывает необходимость проверки цепочки редакций. Предлагаемой строки нет.

Дополнительная попытка получения МО, 12.11.2026:

- Исходный `mosreg.ru/upload/iblock/b9d/713_30.pdf` повторно запрошен HTTP/HTTPS, с параметром загрузки и обычным User-Agent: получен HTML `Forbidden`, не PDF. Подтверждённая официальная карточка не раскрывает сам порог.
- [Официальная муниципальная копия Ступино](https://stupinoadm.ru/export/sites/stupinoadm/dokumenty/.galleries/files/5806-p.pdf) читается, но это самостоятельные МНГП Ступино, а не консолидированный региональный акт. Территорию действия расширять на область нельзя. Веб-извлечение не показало дату/номер в скане первой страницы, поэтому структурированной строки нет.
- [Документ Мособлархитектуры на официальном сайте Дубны](https://naukograd-dubna.ru/files/2024/12/13/02.08.2024_112%D0%92%D1%85-10539_%D0%93%D0%BE%D1%80%D0%B4%D0%B8%D0%B5%D0%BD%D0%BA%D0%BE_%D0%92.%D0%92._%D0%A2%D0%B8%D1%85%D0%BE%D0%BC%D0%B8%D1%80%D0%BE%D0%B2_%D0%9C.%D0%90..pdf) содержит письмо от 02.08.2024 и проекты поправок с незаполненными датами/номерами. Проекты не являются основанием для порога.
- При дальнейшем чтении п.5.23.1 следует отличать расстояние **остановка→МФЦ** от доступности **жильё→МФЦ**. Число 300 м из сторонней копии не проверено по региональному первоисточнику и не соответствует второй метрике. Нормативной JSON-строки нет.

Москву город в этом коротком проходе не исследовали. Универсальное значение 60 мин не установлено ни для одного из четырёх индексов.
