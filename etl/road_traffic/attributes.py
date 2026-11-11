import json
import re
from typing import Any

LANE_KEYS = {
    "lanes": "lanes_total",
    "lanes:forward": "lanes_forward",
    "lanes:backward": "lanes_backward",
    "lanes:both_ways": "lanes_both_ways",
}
SPEED_KEYS = {
    "maxspeed": "maxspeed_kmh",
    "maxspeed:forward": "maxspeed_forward_kmh",
    "maxspeed:backward": "maxspeed_backward_kmh",
}


def _status(statuses: list[str]) -> str:
    for status in ["contradictory", "invalid", "ambiguous", "valid"]:
        if status in statuses:
            return status
    return "missing"


def _lanes(value: object, allow_zero: bool) -> tuple[int | None, str]:
    if value is None or str(value).strip() == "":
        return None, "missing"
    raw = str(value).strip()
    if any(separator in raw for separator in [";", "|", "@"]):
        return None, "ambiguous"
    if not re.fullmatch(r"\d+", raw):
        return None, "invalid"
    count = int(raw)
    if count == 0 and not allow_zero:
        return None, "invalid"
    if count > 65535:
        return None, "invalid"
    return count, "valid"


def _speed(value: object) -> tuple[float | None, str]:
    if value is None or str(value).strip() == "":
        return None, "missing"
    raw = str(value).strip().lower()
    if (
        raw
        in {
            "none",
            "signals",
            "variable",
            "walk",
            "national",
            "urban",
            "rural",
            "unposted",
            "implicit",
            "notsigned",
            "default",
        }
        or ":" in raw
    ):
        return None, "ambiguous"
    if any(separator in raw for separator in [";", "|", "@"]):
        return None, "ambiguous"
    match = re.fullmatch(r"(\d+(?:\.\d+)?)\s*(mph|km/h|kmh|kph)?", raw)
    if match is None:
        return None, "invalid"
    value = float(match[1])
    if value <= 0:
        return None, "invalid"
    return value * (1.609344 if match[2] == "mph" else 1.0), "valid"


def _direction(tags: dict[str, Any]) -> tuple[str, str]:
    raw = str(tags.get("oneway") or "").strip().lower()
    if not raw:
        if tags.get("junction") == "roundabout":
            return "forward", "implied"
        return "unknown", "unknown"
    values = {
        "yes": "forward",
        "true": "forward",
        "1": "forward",
        "-1": "reverse",
        "no": "bidirectional",
        "false": "bidirectional",
        "0": "bidirectional",
        "reversible": "reversible",
        "alternating": "alternating",
    }
    if raw in values:
        return values[raw], "explicit"
    if any(separator in raw for separator in [";", "|", "@"]):
        return "unknown", "ambiguous"
    return "unknown", "invalid"


def normalize_way(row: dict[str, Any]) -> dict[str, Any]:
    original = row.get("source_tags", row.get("tags_json"))
    quality = []
    try:
        tags = (
            json.loads(original) if isinstance(original, str) and original else original
        )
        if tags is None:
            tags = {}
        if not isinstance(tags, dict):
            raise TypeError("OSM tags are not an object")
    except (ValueError, TypeError):
        tags = {}
        quality.append("source_tags:invalid")
    tags = dict(tags)
    for key in ["oneway", "highway", "junction"]:
        if key not in tags and row.get(key) is not None:
            tags[key] = row[key]
    result = {
        key: row.get(key)
        for key in ["way_id", "way_idx", "highway", "ref", "name", "km"]
    }
    result["source_tags"] = original
    result["raw_tags"] = tags
    statuses = []
    for tag, key in LANE_KEYS.items():
        value, status = _lanes(tags.get(tag), tag != "lanes")
        result[key] = value
        statuses.append(status)
        if status in {"invalid", "ambiguous"}:
            quality.append(f"{tag}:{status}")
    total = result["lanes_total"]
    directional = [
        result[key] for key in ["lanes_forward", "lanes_backward", "lanes_both_ways"]
    ]
    known_sum = sum(value for value in directional if value is not None)
    if total is not None and (
        known_sum > total
        or (all(value is not None for value in directional) and known_sum != total)
    ):
        statuses.append("contradictory")
        quality.append("lanes:directional_sum_conflict")
    result["oneway"], result["direction_status"] = _direction(tags)
    if result["direction_status"] in {"ambiguous", "invalid"}:
        quality.append("oneway:" + result["direction_status"])
    wrong = "lanes_backward" if result["oneway"] == "forward" else "lanes_forward"
    if result["oneway"] in {"forward", "reverse"} and result[wrong] not in {None, 0}:
        statuses.append("contradictory")
        quality.append("lanes:oneway_conflict")
    if result["oneway"] in {"forward", "reverse"} and result["lanes_both_ways"] not in {
        None,
        0,
    }:
        statuses.append("contradictory")
        quality.append("lanes:shared_oneway_conflict")
    result["lanes_status"] = _status(statuses)
    speed_statuses = []
    for tag, key in SPEED_KEYS.items():
        value, status = _speed(tags.get(tag))
        result[key] = value
        speed_statuses.append(status)
        if status in {"invalid", "ambiguous"}:
            quality.append(f"{tag}:{status}")
    result["maxspeed_status"] = _status(speed_statuses)
    if any(
        key.endswith(":conditional")
        for key in tags
        if key.startswith(("lanes", "oneway", "maxspeed"))
    ):
        quality.append("conditional_attributes_present")
    result["quality"] = quality
    return result
