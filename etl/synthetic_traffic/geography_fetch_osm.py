from shapely.geometry import LineString, Polygon
from shapely.ops import polygonize, unary_union


def osm_geometry(element, resolution):
    if element["type"] == "way":
        coordinates = [
            (point["lon"], point["lat"]) for point in element.get("geometry", [])
        ]
        if len(coordinates) < 2:
            raise ValueError(f"Incomplete OSM way {element['id']}")
        if coordinates[0] == coordinates[-1] and len(coordinates) >= 4:
            result = Polygon(coordinates)
        elif "waterway" in element.get("tags", {}):
            result = LineString(coordinates).buffer(resolution / 2)
        else:
            raise ValueError(f"Unclosed OSM area {element['id']}")
    elif element.get("tags", {}).get("type") == "waterway":
        lines = [
            LineString([(p["lon"], p["lat"]) for p in m["geometry"]])
            for m in element.get("members", [])
            if m.get("type") == "way" and len(m.get("geometry", [])) >= 2
        ]
        result = unary_union(lines).buffer(resolution / 2)
    else:
        rings = {"outer": [], "inner": []}
        for member in element.get("members", []):
            if member.get("type") != "way":
                continue
            role = member.get("role") or "outer"
            if role not in rings:
                continue
            coordinates = [
                (point["lon"], point["lat"]) for point in member.get("geometry", [])
            ]
            if len(coordinates) < 2:
                raise ValueError(f"Incomplete OSM relation {element['id']}")
            rings[role].append(LineString(coordinates))
        outer = list(polygonize(unary_union(rings["outer"])))
        inner = list(polygonize(unary_union(rings["inner"])))
        if not outer:
            raise ValueError(f"OSM relation {element['id']} has no complete outer ring")
        result = unary_union(outer).difference(unary_union(inner))
    if result.is_empty or not result.is_valid:
        raise ValueError(f"Invalid OSM area {element['id']}")
    return result
