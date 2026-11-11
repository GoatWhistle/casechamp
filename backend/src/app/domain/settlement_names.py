import re


def normalized_place(value: str) -> str:
    return " ".join(value.casefold().replace("ё", "е").split())


def settlement_name(value: str) -> str:
    return re.sub(
        r"^(?:г\.|г\s|город\s|село\s|деревня\s|поселок\s|хутор\s|станица\s|пгт\.?\s)\s*",
        "",
        normalized_place(value),
        count=1,
    )


def settlement_query(value: str) -> tuple[str, str]:
    name, _, region = value.partition(",")
    return normalized_place(name), normalized_place(region)


def matching_places(places: list[tuple[str, str]], query: str) -> list[int]:
    name, region = settlement_query(query)
    candidates = [
        i for i, (_, area) in enumerate(places) if not region or normalized_place(area) == region
    ]
    exact = [i for i in candidates if normalized_place(places[i][0]) == name]
    if exact:
        return exact
    return [i for i in candidates if settlement_name(places[i][0]) == settlement_name(name)]
