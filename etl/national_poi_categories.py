import re


def categories(tags: dict[str, str]) -> list[str]:
    result = []
    amenity = tags.get("amenity")
    direct = {"school": "school", "library": "library", "fire_station": "fire",
              "bus_station": "bus_station", "hospital": "medical", "clinic": "medical"}
    if amenity in direct:
        result.append(direct[amenity])
    if tags.get("healthcare") in {"hospital", "clinic"} and "medical" not in result:
        result.append("medical")
    if tags.get("highway") == "bus_stop" or (tags.get("public_transport") == "platform" and tags.get("bus") == "yes"):
        result.append("stop")
    if tags.get("office") == "employment_agency":
        result.append("employment_candidate")
    name = tags.get("name", "").casefold()
    if tags.get("office") == "mfc" or (tags.get("office") == "government" and re.search(r"\bмфц\b|мои документы|многофункциональн", name)):
        result.append("mfc_candidate")
    return result
