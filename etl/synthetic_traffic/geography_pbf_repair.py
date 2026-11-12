import hashlib
import json
import os
import shutil
import sqlite3
import uuid
import xml.etree.ElementTree as ET
from datetime import UTC, datetime
from pathlib import Path

from shapely import make_valid
from shapely.geometry import LineString, Polygon
from shapely.ops import polygonize_full, unary_union
from synthetic_traffic.geography_fetch_osm import osm_geometry


def repaired_geometry(path, kind, osm_id):
    document = ET.fromstring(Path(path).read_bytes())
    nodes = {
        int(node.attrib["id"]): {
            "lon": float(node.attrib["lon"]),
            "lat": float(node.attrib["lat"]),
        }
        for node in document.findall("node")
    }
    ways = {int(way.attrib["id"]): way for way in document.findall("way")}
    element = document.find(f"{kind}[@id='{osm_id}']")
    if element is None:
        raise ValueError(f"Repair source does not contain {kind}/{osm_id}")
    tags = {tag.attrib["k"]: tag.attrib["v"] for tag in element.findall("tag")}
    result = {"type": kind, "id": osm_id, "tags": tags}

    def coordinates(way):
        return [nodes[int(node.attrib["ref"])] for node in way.findall("nd")]

    topology_repair = None
    conservative_outer = []
    if kind == "way":
        result["geometry"] = coordinates(element)
        points = [(point["lon"], point["lat"]) for point in result["geometry"]]
        if len(points) >= 4 and points[0] == points[-1]:
            candidate = Polygon(points)
            if not candidate.is_valid:
                candidate = make_valid(candidate)
                if (
                    candidate.geom_type in {"Polygon", "MultiPolygon"}
                    and not candidate.is_empty
                ):
                    topology_repair = candidate

    else:
        members = []
        rings = {"outer": [], "inner": []}
        for member in element.findall("member"):
            role = member.attrib.get("role", "") or "outer"
            if role not in rings:
                continue
            if member.attrib["type"] != "way":
                raise ValueError("Repair requires complete direct way members")
            geometry = coordinates(ways[int(member.attrib["ref"])])
            members.append({"type": "way", "role": role, "geometry": geometry})
            rings[role].append(
                LineString([(node["lon"], node["lat"]) for node in geometry])
            )
        for role, lines in rings.items():
            if not lines:
                continue
            closed, cuts, dangles, invalid = polygonize_full(lines)
            if cuts.is_empty and dangles.is_empty and invalid.is_empty:
                continue
            if (
                role != "outer"
                or tags.get("natural") != "water"
                or closed.is_empty
                or not cuts.is_empty
                or not invalid.is_empty
                or dangles.length > 0.002
                or unary_union(closed).boundary.distance(dangles) > 1e-10
            ):
                raise ValueError("Repair relation contains incomplete polygon rings")
            conservative_outer.append(dangles.buffer(0.0005))
        result["members"] = members
    geometry = (
        topology_repair if topology_repair is not None else osm_geometry(result, 0.001)
    )
    if conservative_outer:
        geometry = geometry.union(unary_union(conservative_outer))
    if (
        geometry.geom_type not in {"Polygon", "MultiPolygon"}
        or geometry.is_empty
        or not geometry.is_valid
    ):
        raise ValueError("Repair did not produce a valid complete area")
    return geometry, {
        "osm_version": element.attrib.get("version"),
        "osm_timestamp": element.attrib.get("timestamp"),
        "tags": tags,
        "topology_repair": "closed_source_rings_plus_conservative_dangling_outer_water_member_buffer"
        if conservative_outer
        else "make_valid_recorded_closed_ring"
        if topology_repair is not None
        else None,
        "conservative_member_buffer_degrees": 0.0005 if conservative_outer else None,
    }


def repair_vector_cache(incomplete, target, repair_directory):
    incomplete, target, directory = (
        Path(incomplete),
        Path(target),
        Path(repair_directory),
    )
    if target.exists():
        raise ValueError("A completed vector cache already exists at this path")
    with sqlite3.connect(f"file:{incomplete}?mode=ro", uri=True) as connection:
        manifest = json.loads(
            connection.execute(
                "SELECT value FROM metadata WHERE key='manifest'"
            ).fetchone()[0]
        )
    if manifest.get("status") != "incomplete":
        raise ValueError("Repair requires an explicitly incomplete cache")
    repaired = []
    for missing in manifest["missing_areas"]:
        layer, kind, osm_id = missing["layer"], missing["kind"], missing["osm_id"]
        source = directory / f"{osm_id}.osm"
        geometry, metadata = repaired_geometry(source, kind, osm_id)
        tags = metadata["tags"]
        if (
            layer == "protected"
            and tags.get("boundary") != "protected_area"
            and tags.get("leisure") != "nature_reserve"
        ):
            raise ValueError(
                "Current repair object no longer matches the protected source layer"
            )
        repaired.append(
            (
                layer,
                kind,
                osm_id,
                geometry,
                {
                    "url": f"https://api.openstreetmap.org/api/0.6/{kind}/{osm_id}/full",
                    "sha256": hashlib.sha256(source.read_bytes()).hexdigest(),
                    **metadata,
                },
            )
        )
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_name(target.name + f".{uuid.uuid4().hex}.repairing")
    shutil.copyfile(incomplete, temporary)
    connection = sqlite3.connect(temporary)
    try:
        for layer, kind, osm_id, geometry, _ in repaired:
            cursor = connection.execute(
                "INSERT INTO features(layer,kind,osm_id,basis,wkb) VALUES (?,?,?,?,?)",
                (
                    layer,
                    kind,
                    osm_id,
                    "official_osm_api_complete_area_repair",
                    geometry.wkb,
                ),
            )
            west, south, east, north = geometry.bounds
            connection.execute(
                "INSERT INTO spatial VALUES (?,?,?,?,?)",
                (cursor.lastrowid, west, east, south, north),
            )
            connection.execute(
                "DELETE FROM expected WHERE layer=? AND kind=? AND osm_id=?",
                (layer, kind, osm_id),
            )
            manifest["features"][layer] += 1
        if connection.execute("SELECT count(*) FROM expected").fetchone()[0]:
            raise ValueError("Unresolved source areas remain after repair")
        manifest.update(
            status="complete",
            missing_areas=[],
            repaired_at=datetime.now(UTC).isoformat(),
            snapshot_basis="mixed_original_pbf_and_current_official_osm_api",
            repairs=[
                {"layer": layer, "kind": kind, "osm_id": osm_id, **metadata}
                for layer, kind, osm_id, _, metadata in repaired
            ],
        )
        connection.execute(
            "UPDATE metadata SET value=? WHERE key='manifest'", (json.dumps(manifest),)
        )
        connection.commit()
        if connection.execute("PRAGMA quick_check").fetchone()[0] != "ok":
            raise ValueError("Repaired vector cache failed SQLite integrity check")
        connection.close()
        os.replace(temporary, target)
        return manifest
    except BaseException:
        connection.close()
        temporary.unlink(missing_ok=True)
        temporary.with_name(temporary.name + "-journal").unlink(missing_ok=True)
        raise
