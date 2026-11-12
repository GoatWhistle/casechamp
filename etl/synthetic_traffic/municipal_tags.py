from urllib.parse import urlsplit


def municipal_source_confirmed(tags):
    fields = {
        "name",
        "official_name",
        "alt_name",
        "description",
        "official_status",
        "designation",
    }
    coded = any(
        tags.get(key) for key in ("omkmo:code", "ref:oktmo", "oktmo", "oktmo:code")
    )
    explicit = any(
        "муниципал" in value.casefold() for key, value in tags.items() if key in fields
    )
    try:
        legal_url = urlsplit(tags.get("url", ""))
    except ValueError:
        return coded or explicit
    linked_city_municipality = (
        tags.get("addr:region") == "Санкт-Петербург"
        and tags.get("official_status") in {"ru:город", "ru:посёлок"}
        and legal_url.hostname in {"www.gov.spb.ru", "gov.spb.ru"}
        and legal_url.path == "/law"
    )
    official_city_name = (
        tags.get("addr:region") == "Санкт-Петербург"
        and tags.get("official_status") == "ru:город"
        and tags.get("name")
        in {
            "Зеленогорск",
            "Колпино",
            "Красное Село",
            "Кронштадт",
            "Ломоносов",
            "Павловск",
            "Петергоф",
            "Пушкин",
            "Сестрорецк",
        }
    )
    return coded or explicit or linked_city_municipality or official_city_name
