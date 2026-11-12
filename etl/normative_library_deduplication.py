import re


def address_key(value: str) -> str:
    value = value.lower().replace("ё", "е")
    value = re.sub(r"(?<!\d)\d{6}(?!\d)", "", value)
    value = re.sub(r"курганская\s*(?:область|обл\.?)", "", value)
    value = re.sub(r"(?<!\w)(?:г|с|д|ул|п|пос|рп)\.", "", value)
    value = re.sub(r"\b(?:город|село|деревня|улица|дом|район|округ|мо)\b|р-н|р-он", "", value)
    return re.sub(r"[^а-яa-z0-9/]", "", value)


def identity_key(value: str) -> str:
    value = re.sub(r"\([^)]*\d{4}[^)]*\)", "", value)
    value = re.sub(r"^(?:МБУК?|МКУК?|МУК|ГБУК|ГУК)\b\s*[«\"]?", "", value, flags=re.IGNORECASE)
    value = re.split(
        r"\b(?:МБУК?|МКУК?|МУК|ГБУК|ГУК)\b|структурное подразделение|филиал",
        value,
        maxsplit=1,
        flags=re.IGNORECASE,
    )[0]
    named = re.search(r"\bим(?:\.|ени)\s*(.+)", value, re.IGNORECASE)
    if named:
        words = re.findall(r"[а-яё]{4,}", named[1].lower())
        if words:
            return words[-1].replace("ё", "е")
    return re.sub(r"[^а-яa-z0-9]", "", value.lower().replace("ё", "е"))


def deduplicate(facilities: list[dict], existing: list[dict]) -> tuple[list[dict], list[dict]]:
    known = {}
    for row in existing:
        key = (row["service"], identity_key(row["name"]), address_key(row["address"]))
        if all(key):
            known.setdefault(key, row["id"])
    result = []
    aliases = []
    for row in sorted(facilities, key=lambda r: (r["published_on"] or "", r["id"]), reverse=True):
        key = (row["service"], identity_key(row["name"]), address_key(row["address"]))
        if all(key) and key in known:
            aliases.append(
                {
                    "source_url": row["source_url"],
                    "retained_id": known[key],
                    "reason": "same_profile_name_address",
                }
            )
        else:
            result.append(row)
            if all(key):
                known[key] = row["id"]
    return sorted(result, key=lambda r: r["id"]), aliases
