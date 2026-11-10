import re

from app.domain.settlement_names import normalized_place

ABBREVIATIONS = {
    "янао": "ямало-ненецкий автономный округ",
    "хмао": "ханты-мансийский автономный округ",
    "нао": "ненецкий автономный округ",
    "чао": "чукотский автономный округ",
    "еао": "еврейская автономная область",
    "кбр": "кабардино-балкарская республика",
    "кчр": "карачаево-черкесская республика",
    "рсо": "северная осетия",
    "мо": "московская область",
    "ло": "ленинградская область",
    "спб": "санкт-петербург",
}


def region_key(value: str) -> str:
    text = normalized_place(value).replace("—", " ").replace("-", " ")
    text = re.sub(r"\bао\b", "автономный округ", text)
    return " ".join(text.split())


def canonical_region(value: str, names: list[str]) -> str | None:
    query = region_key(ABBREVIATIONS.get(normalized_place(value), value))
    if not query:
        return None
    keys = {name: region_key(name) for name in names}
    exact = [name for name, key in keys.items() if key == query]
    if exact:
        return exact[0]
    contained = [name for name, key in keys.items() if query in key]
    return contained[0] if len(contained) == 1 else None
