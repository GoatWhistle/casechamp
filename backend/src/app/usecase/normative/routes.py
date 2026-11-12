from math import isclose

from app.domain.errors import DataUnavailable, InvalidQuery
from app.domain.normative.model import Origin
from app.usecase.normative.interface import (
    NormativeFireRouting,
    NormativeRepository,
    NormativeRouting,
)
from app.usecase.normative.route import TRACE_MODEL_REVISIONS, NormativeRoute, RouteStage
from app.usecase.normative.routing import routing_for


class NormativeRoutes:
    def __init__(
        self,
        repository: NormativeRepository,
        road: NormativeRouting | None,
        walking: NormativeRouting | None,
        fire: NormativeFireRouting | None = None,
    ) -> None:
        self.repository = repository
        self.road = road
        self.walking = walking
        self.fire = fire

    def get(self, run_id: str, origin_id: str, stage: RouteStage) -> NormativeRoute:
        saved = self.repository.route_context(run_id, origin_id, stage)
        if saved is None:
            raise InvalidQuery("Unknown saved normative assessment")
        if saved.model_revision not in TRACE_MODEL_REVISIONS:
            raise DataUnavailable("Recalculate the unversioned assessment before tracing a route")
        row = saved.origin
        facility = saved.facility
        if facility is None or row.routing_node is None or row.approach_metres is None:
            raise DataUnavailable("No reconstructable route is stored for this origin")
        routing = routing_for(
            saved.criterion, self.road, self.walking, self.fire, saved.fire_profile
        )
        origin = Origin(
            row.id,
            row.name,
            row.population,
            row.routing_node,
            row.approach_metres / 1000,
            row.latitude,
            row.longitude,
        )
        closed = saved.closed_way_ids if stage == "scenario" else []
        traced = routing.trace(origin, facility, closed, saved.graph_revision)
        actual = traced.distance_metres if saved.criterion.unit == "metres" else traced.minutes
        expected = row.distance_metres if saved.criterion.unit == "metres" else row.minutes
        if (
            actual is None
            or expected is None
            or not isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-4)
        ):
            raise DataUnavailable("The reconstructed route does not match the saved cost")
        return NormativeRoute(
            run_id,
            origin_id,
            facility.id,
            stage,
            saved.graph_revision,
            saved.model_revision,
            traced,
        )
