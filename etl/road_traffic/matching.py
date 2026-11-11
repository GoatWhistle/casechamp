import re
from collections.abc import Iterable
from math import isfinite

from pyproj import CRS, Transformer
from shapely.geometry import LineString, Point

from .geography import unwrap


def name_key(value: object) -> str:
    text = str(value or "").lower().replace("ё", "е").strip()
    text = re.sub(r"^(улица|ул[.]?|проспект|пр-т|переулок|пер[.]?)\s+", "", text)
    return re.sub(r"[^a-zа-я0-9]", "", text)


def observation_keys(observation: dict) -> tuple[str, ...]:
    values = [observation.get("road_name"), observation.get("ref")]
    values.extend(observation.get("candidate_road_names", []))
    site = str(observation.get("site") or "")
    first = re.split(
        r"\(|/|пересечение|перекр[её]сток", site, maxsplit=1, flags=re.IGNORECASE
    )[0]
    first = re.sub(r"^\s*\d+[.)]?\s+", "", first).strip()
    if (
        len(name_key(first)) >= 5
        and not first.isdigit()
        and not re.fullmatch(r"survey site \d+", first)
    ):
        values.append(first)
    return tuple(sorted({name_key(value) for value in values if name_key(value)}))


def coordinate_distance(observation: dict, road: dict) -> float | None:
    lon, lat = observation.get("lon"), observation.get("lat")
    if lon is None or lat is None or not road.get("coordinates"):
        return None
    lon, lat = float(lon), float(lat)
    if not isfinite(lon) or not isfinite(lat) or not -90 <= lat <= 90:
        raise ValueError("Invalid observation coordinates")
    projection = CRS.from_proj4(f"+proj=aeqd +lat_0={lat} +lon_0={lon} +datum=WGS84")
    transformer = Transformer.from_crs("EPSG:4326", projection, always_xy=True)
    coordinates = unwrap(road["coordinates"])
    xs, ys = transformer.transform(*zip(*coordinates))
    line = LineString(zip(xs, ys))
    point = Point(*transformer.transform(lon, lat))
    return point.distance(line)


def match_observations(
    observations: list[dict],
    roads: Iterable[dict],
    graph_revision: str,
    confirmations: list[dict] | None = None,
) -> list[dict]:
    if not graph_revision:
        raise ValueError("Graph revision is required")
    identifiers = {str(row["observation_id"]) for row in observations}
    if len(identifiers) != len(observations):
        raise ValueError("Duplicate observation identifier")
    approved = {}
    for confirmation in confirmations or []:
        key = (str(confirmation["observation_id"]), int(confirmation["way_id"]))
        if key[0] not in identifiers:
            raise ValueError("Confirmation references an unknown observation")
        if confirmation.get("graph_revision") != graph_revision:
            raise ValueError("Confirmation graph revision mismatch")
        if not str(confirmation.get("evidence", "")).strip():
            raise ValueError("Confirmation evidence is required")
        if key in approved:
            raise ValueError("Duplicate confirmation")
        approved[key] = confirmation
    keys = {
        str(row["observation_id"]): set(observation_keys(row)) for row in observations
    }
    candidates = {str(row["observation_id"]): {} for row in observations}
    for road in roads:
        way_id = int(road["way_id"])
        road_names = {name_key(road.get("name")), name_key(road.get("ref"))} - {""}
        for observation in observations:
            observation_id = str(observation["observation_id"])
            same_name = bool(road_names & keys[observation_id])
            same_region = not road.get("region_id") or (
                str(road["region_id"]) == str(observation.get("region_id"))
            )
            confirmation = approved.get((observation_id, way_id))
            if not same_region and not confirmation:
                continue
            distance = coordinate_distance(observation, road)
            if not confirmation and not (
                same_region
                and (same_name or (distance is not None and distance <= 100))
            ):
                continue
            item = {
                "observation_id": observation_id,
                "graph_revision": graph_revision,
                "way_id": way_id,
                "status": "confirmed" if confirmation else "candidate",
                "method": "manual_review"
                if confirmation
                else (
                    "road_name_and_coordinates"
                    if same_name and distance is not None
                    else "road_name"
                    if same_name
                    else "coordinates_within_100m"
                ),
                "distance_m": distance,
                "direction": confirmation.get("direction", observation.get("direction"))
                if confirmation
                else observation.get("direction"),
                "evidence": confirmation["evidence"] if confirmation else "",
                "extent": confirmation.get("extent", "point")
                if confirmation
                else "point",
            }
            previous = candidates[observation_id].get(way_id)
            if previous is None or (
                distance is not None
                and (
                    previous["distance_m"] is None or distance < previous["distance_m"]
                )
            ):
                candidates[observation_id][way_id] = item
    missing = set(approved) - {
        (row["observation_id"], row["way_id"])
        for group in candidates.values()
        for row in group.values()
        if row["status"] == "confirmed"
    }
    if missing:
        raise ValueError("Confirmed road is absent from the supplied graph candidates")
    result = []
    for observation in observations:
        observation_id = str(observation["observation_id"])
        matches = list(candidates[observation_id].values())
        result.extend(
            sorted(
                matches,
                key=lambda row: (
                    row["status"] != "confirmed",
                    row["distance_m"] is None,
                    row["distance_m"] or 0,
                    row["way_id"],
                ),
            )
            or [
                {
                    "observation_id": observation_id,
                    "graph_revision": graph_revision,
                    "way_id": None,
                    "status": "unmatched",
                    "method": "insufficient_location",
                    "distance_m": None,
                    "direction": observation.get("direction"),
                    "evidence": "",
                    "extent": "point",
                }
            ]
        )
    return result
