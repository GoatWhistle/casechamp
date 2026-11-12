from math import isclose

from app.domain.errors import DataUnavailable, InvalidQuery
from app.domain.normative.model import Origin
from app.usecase.normative.interface import NormativeFireRouting, NormativeRouting
from app.usecase.normative.regional_models import RegionalWalkingModels, regional_model
from app.usecase.normative.regional_view import (
    RegionalPointDetail,
    RegionalRunView,
    RegionalViewRepository,
)
from app.usecase.normative.route import NormativeRoute, RouteStage


class RegionalRouteQueries:
    def __init__(
        self,
        views: RegionalViewRepository,
        road: NormativeRouting | None,
        walking: RegionalWalkingModels | None,
        fire: NormativeFireRouting | None,
    ) -> None:
        self.views = views
        self.road = road
        self.walking = walking
        self.fire = fire

    def route(self, run_id: str, origin_id: str, stage: RouteStage) -> NormativeRoute:
        view = self.views.view(run_id)
        if view is None:
            raise InvalidQuery("Unknown regional measurement")
        point = self.views.point(view, stage, origin_id)
        if point is None:
            raise InvalidQuery("Unknown regional measurement origin")
        return trace_regional_route(view, point, stage, self.road, self.walking, self.fire)


def trace_regional_route(
    view: RegionalRunView,
    point: RegionalPointDetail,
    stage: RouteStage,
    road: NormativeRouting | None,
    walking: RegionalWalkingModels | None,
    fire: NormativeFireRouting | None,
) -> NormativeRoute:
    model = regional_model(
        view.criterion_id, view.region_id, road, walking, fire, view.fire_profile
    )
    if (
        view.model_revision != model.revision
        or view.measurement_definition != model.measurement_definition
    ):
        raise DataUnavailable("The regional measurement routing model is unavailable")
    row, facility = point.row, point.facility
    if facility is None or row.routing_node is None or row.approach_metres is None:
        raise DataUnavailable("No reconstructable regional route is stored")
    origin = Origin(
        row.id,
        row.name,
        row.population,
        row.routing_node,
        row.approach_metres / 1000,
        row.latitude,
        row.longitude,
    )
    closed = view.closed_way_ids if stage == "scenario" else []
    geometry = model.routing.trace(origin, facility, closed, view.graph_revision)
    actual = geometry.distance_metres if model.unit == "metres" else geometry.minutes
    expected = row.distance_metres if model.unit == "metres" else row.minutes
    if (
        actual is None
        or expected is None
        or not isclose(actual, expected, rel_tol=1e-9, abs_tol=1e-4)
    ):
        raise DataUnavailable("The regional route differs from its saved measurement")
    return NormativeRoute(
        view.run_id, row.id, facility.id, stage, view.graph_revision, view.model_revision, geometry
    )
