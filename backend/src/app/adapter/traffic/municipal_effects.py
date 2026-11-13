from synthetic_traffic.assignment import Assignment
from synthetic_traffic.model import Network, Trip

from app.adapter.traffic.municipal_membership import municipal_edge_indices
from app.domain.municipal_metrics import municipal_contains
from app.usecase.municipal_scenarios import MunicipalTrafficMetrics
from app.usecase.municipalities import Municipality


def municipal_traffic_metrics(municipality: Municipality, network: Network,
                              assignment: Assignment, trips: list[Trip]) -> MunicipalTrafficMetrics:
    selected = municipal_edge_indices(municipality, network)
    origins = {trip.origin for trip, hours in zip(trips, assignment.od_hours, strict=True) if hours is None}
    local_origins = {origin for origin in origins if municipal_contains(
        float(network.lon[origin]), float(network.lat[origin]), municipality.coordinates)}
    unserved = sum(trip.vehicles_per_hour for trip, hours in zip(trips, assignment.od_hours, strict=True)
                   if hours is None and trip.origin in local_origins)
    return MunicipalTrafficMetrics(float(assignment.flow[selected] @ assignment.hours[selected]),
                                   int((assignment.ratio[selected] > 1).sum()), unserved)
