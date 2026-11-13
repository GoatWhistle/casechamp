import numpy as np
from shapely import points
from synthetic_traffic.model import Network

from app.adapter.municipal.assignment import MunicipalSpatialIndex
from app.domain.municipal_metrics import MunicipalObservation
from app.usecase.municipalities import Municipality

EDGE_BATCH_SIZE = 131072

def municipal_membership(
    municipalities: list[Municipality], observations: list[MunicipalObservation]
) -> dict[str, list[MunicipalObservation]]:
    result: dict[str, list[MunicipalObservation]] = {row.id: [] for row in municipalities}
    if not observations or not municipalities:
        return result
    index = MunicipalSpatialIndex(municipalities)
    coordinates = points([((row.longitude + 180) % 360 - 180, row.latitude) for row in observations])
    matches = index.tree.query(coordinates, predicate="covered_by")
    seen: set[tuple[int, str]] = set()
    for source, target in zip(matches[0], matches[1], strict=True):
        key = int(source), index.owners[int(target)]
        if key not in seen:
            result[key[1]].append(observations[key[0]])
            seen.add(key)
    return result


def municipal_edge_indices(municipality: Municipality, network: Network) -> list[int]:
    index = MunicipalSpatialIndex([municipality])
    bounds = [geometry.bounds for geometry in index.tree.geometries
              if geometry.bounds[0] <= 180 and geometry.bounds[2] >= -180]
    result: list[int] = []
    for start in range(0, len(network.source), EDGE_BATCH_SIZE):
        source = network.source[start:start + EDGE_BATCH_SIZE]
        target = network.target[start:start + EDGE_BATCH_SIZE]
        longitude = network.lon[source] + ((network.lon[target] - network.lon[source] + 180) % 360 - 180) / 2
        longitude = (longitude + 180) % 360 - 180
        latitude = (network.lat[source] + network.lat[target]) / 2
        nearby = np.zeros(len(source), dtype=bool)
        for west, south, east, north in bounds:
            nearby |= (longitude >= west) & (longitude <= east) & (latitude >= south) & (latitude <= north)
        candidates = np.flatnonzero(nearby)
        if not len(candidates):
            continue
        coordinates = points(np.column_stack((longitude[candidates], latitude[candidates])))
        matches = index.tree.query(coordinates, predicate="covered_by")
        result.extend(int(candidates[value]) + start for value in np.unique(matches[0]))
    return result
