import hashlib
import json
import math
import re

from .matching import observation_keys

NORMALIZED_NAME = (
    "replaceRegexpAll(replaceRegexpAll(replaceAll(lowerUTF8(ifNull(name,'')),'ё','е'),"
    "'^(улица|ул[.]?|проспект|пр-т|переулок|пер[.]?)[[:space:]]+',''),'[^a-zа-я0-9]','')"
)
NORMALIZED_REF = NORMALIZED_NAME.replace("ifNull(name,'')", "ifNull(ref,'')")


def literal(value: object) -> str:
    value = str(value).replace("\\", "\\\\").replace("'", "\\'")
    return (
        "'" + value.replace("\n", "\\n").replace("\r", "\\r").replace("\0", "\\0") + "'"
    )


def names(observation: dict) -> tuple[str, ...]:
    return observation_keys(observation)


def coordinate_predicate(observation: dict) -> str | None:
    lon, lat = observation.get("lon"), observation.get("lat")
    if lon is None or lat is None:
        return None
    lon, lat = float(lon), float(lat)
    if not math.isfinite(lon) or not math.isfinite(lat) or not -90 <= lat <= 90:
        raise ValueError("Invalid observation coordinate")
    lon = (lon + 180) % 360 - 180
    left, right = lon - 0.02, lon + 0.02
    if right > 180:
        longitude = f"((min_lon<=180 AND max_lon>={left}) OR (min_lon<={right - 360} AND max_lon>=-180))"
    elif left < -180:
        longitude = f"((min_lon<=180 AND max_lon>={left + 360}) OR (min_lon<={right} AND max_lon>=-180))"
    else:
        longitude = f"(min_lon<={right} AND max_lon>={left})"
    return f"min_lat<={lat + 0.005} AND max_lat>={lat - 0.005} AND {longitude}"


def candidate_roads(
    store, observations: list[dict], snapshot: str, cache_directory=None
) -> list[dict]:
    prefix = "plexus_traffic_snapshot_"
    if not snapshot.startswith(prefix) or not re.fullmatch(r"[A-Za-z0-9_]+", snapshot):
        raise ValueError("Unsupported traffic snapshot identifier")
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", store.database):
        raise ValueError("Unsupported traffic database identifier")
    run_id = snapshot[len(prefix) :]
    if not run_id:
        raise ValueError("Missing traffic run identifier")
    requests = {}
    for observation in observations:
        region_id = str(observation.get("region_id") or "")
        keys = names(observation)
        bbox = coordinate_predicate(observation)
        if region_id and (keys or bbox):
            requests[(region_id, keys, bbox)] = None
    result = []
    for region_id, keys, bbox in requests:
        region_filter = (
            f"SELECT DISTINCT way_id FROM {store.database}.coverage_parts "
            f"WHERE run_id={literal(run_id)} AND region_id={literal(region_id)}"
        )
        restrictions = []
        if keys:
            values = ",".join(literal(key) for key in keys)
            restrictions.append(
                f"way_id IN (SELECT way_id FROM {snapshot}.ways WHERE "
                f"way_id IN ({region_filter}) AND "
                f"({NORMALIZED_NAME} IN ({values}) OR {NORMALIZED_REF} IN ({values})))"
            )
        if bbox:
            restrictions.append(f"({bbox})")
        priority = f"if(({bbox}),0,1)," if bbox else ""
        query = (
            f"SELECT way_id,name,highway,coordinates FROM {snapshot}.road_lines "
            f"WHERE way_id IN ({region_filter}) AND "
            f"({' OR '.join(restrictions)}) ORDER BY {priority}way_id,source_node,target_node LIMIT 500"
        )
        cache_path = None
        if cache_directory is not None:
            cache_directory.mkdir(parents=True, exist_ok=True)
            cache_path = cache_directory / (
                hashlib.sha256(query.encode()).hexdigest() + ".json"
            )
        if cache_path is not None and cache_path.exists():
            roads = json.loads(cache_path.read_text())
        else:
            roads = store.rows(query)
            if cache_path is not None:
                temporary = cache_path.with_suffix(".part")
                temporary.write_text(json.dumps(roads, ensure_ascii=False))
                temporary.replace(cache_path)
        ids = sorted({int(row["way_id"]) for row in roads})
        references = {}
        if ids:
            values = ",".join(map(str, ids))
            references = {
                int(row["way_id"]): row["ref"]
                for row in store.rows(
                    f"SELECT way_id,ref FROM {snapshot}.ways WHERE way_id IN ({values})"
                )
            }
        for road in roads:
            result.append(
                {
                    **road,
                    "ref": references.get(int(road["way_id"])),
                    "region_id": region_id,
                }
            )
    return result
