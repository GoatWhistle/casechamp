from app.adapter.road_graph.data import GraphData
from app.domain.errors import DataUnavailable
from app.usecase.road_geometry import RoadGeometry


class SelectionGeometry:
    def __init__(self, data: GraphData) -> None:
        self.data = data

    def geometry(self, way_ids: list[int]) -> RoadGeometry:
        return selection_geometry(self.data, way_ids)


def selection_geometry(data: GraphData, way_ids: list[int]) -> RoadGeometry:
    rows = data.read("scenario_lines", {"ids": way_ids})
    lengths = {int(row[0]): float(row[2]) for row in rows}
    if set(lengths) != set(way_ids):
        raise DataUnavailable("Geometry is missing for selected OSM ways")
    names = list(dict.fromkeys(str(row[1]) for row in rows))
    lines = [[[float(point[0]), float(point[1])] for point in row[3]] for row in rows]
    return RoadGeometry(names, sum(lengths.values()), lines)
