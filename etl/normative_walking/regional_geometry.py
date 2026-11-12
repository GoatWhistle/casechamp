from shapely.geometry import LineString, MultiLineString


def line_geometry(points: list[tuple[float, float]]) -> LineString | MultiLineString:
    parts = [[points[0]]]
    for left, right in zip(points, points[1:]):
        if abs(left[0] - right[0]) <= 180:
            parts[-1].append(right)
            continue
        border = 180 if left[0] > 0 else -180
        adjusted = right[0] + (360 if border > 0 else -360)
        ratio = (border - left[0]) / (adjusted - left[0])
        latitude = left[1] + ratio * (right[1] - left[1])
        parts[-1].append((border, latitude))
        parts.append([(-border, latitude), right])
    return LineString(parts[0]) if len(parts) == 1 else MultiLineString(parts)
