import re


def normalized(value: str) -> str:
    return re.sub(r"[^а-яa-z0-9/]", "", value.lower().replace("ё", "е"))


def address_matches(source: str, candidate: dict[str, str]) -> bool:
    source = re.sub(r"^(?:м\.о\.|г\.о\.)[^,]+,", "", source)
    source = re.split(r",?\s*(?:помещ|этаж|ТРЦ)", source)[0]
    locality = re.search(
        r"(?<!\w)(?:г\.(?!о\.)|с\.|рп\b|р\.п\.)\s*([^,]+?)(?=,|\s+ул\.|$)", source
    )
    street = re.search(r"(?:ул\.|улица|пер\.|переулок|проспект)\s*([^,]+)", source)
    houses = re.findall(r",\s*(?:(?:д|зд|стр)\.\s*|здание\s*)?(\d[\w/-]*)\s*(?=,|$)", source)
    if locality is None or street is None or not houses:
        return False
    places = [candidate.get(key, "") for key in ("city", "town", "village", "hamlet")]
    if normalized(locality[1]) not in {normalized(place) for place in places if place}:
        return False
    if normalized(houses[-1]) != normalized(candidate.get("house_number", "")):
        return False
    road = candidate.get("road", "")
    street_type = "переулок" if re.search(r"(?:пер\.|переулок)", street[0]) else "улица"
    if street_type not in road.lower():
        return False
    return normalized(street[1]) == normalized(road.replace(street_type, ""))
