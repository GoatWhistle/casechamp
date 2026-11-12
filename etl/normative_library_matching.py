import re

from normative_address import address_matches


def library_address_matches(address: str, tags: dict[str, str]) -> bool:
    postcode = re.search(r"(?<!\d)\d{6}(?!\d)", address)
    if postcode is None or tags.get("addr:postcode") != postcode[0]:
        return False
    value = re.sub(r"(?<!\w)(?:город)\s+", "г. ", address, flags=re.IGNORECASE)
    value = re.sub(r"(?<!\w)(?:село|деревня)\s+", "с. ", value, flags=re.IGNORECASE)
    value = re.sub(r"(?<!\w)(?:д\.|п\.|пос\.)\s*(?=[а-яё])", "с. ", value, flags=re.IGNORECASE)
    value = re.sub(r"\bдом\s+", "д. ", value, flags=re.IGNORECASE)
    value = re.sub(r"№\s*", "", value)
    value = re.sub(r"(\d)\s+([а-яёa-z])(?=\s*$)", r"\1\2", value, flags=re.IGNORECASE)
    value = re.sub(r"((?:ул\.|улица|пер\.)[^,]+?)\s+(\d+[\w/-]*)\s*$", r"\1, \2", value)
    candidate = {
        "village": tags.get("addr:city", ""),
        "house_number": tags.get("addr:housenumber", ""),
        "road": tags.get("addr:street", ""),
    }
    return address_matches(value, candidate)
