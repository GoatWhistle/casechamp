from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Protocol
from uuid import uuid4

from app.domain.errors import DataUnavailable, InvalidQuery
from app.domain.normative.comparison import RouteComparison, compare_routes
from app.domain.normative.fire import FireProfile
from app.domain.normative.measurement_definition import MeasurementDefinition
from app.domain.normative.model import AccessRow, Facility, Origin, Uncertainty
from app.usecase.normative.interface import NormativeFireRouting, NormativeRouting
from app.usecase.normative.regional_catalog import RegionalCatalogQueries
from app.usecase.normative.regional_models import (
    REGIONAL_ROAD_REVISION,
    RegionalWalkingModels,
    regional_model,
)
from app.usecase.normative.regional_receipt import (
    RegionalMeasurementHead,
    RegionalMeasurementReceipt,
)
from app.usecase.normative.regional_route import RegionalRouteQueries, trace_regional_route
from app.usecase.normative.regional_view import (
    RegionalPointDetail,
    RegionalRunView,
    RegionalViewRepository,
)
from app.usecase.normative.route import NormativeRoute, RouteStage


@dataclass(frozen=True, slots=True)
class RegionalMeasurement:
    run_id: str
    region_id: str
    region_name: str
    criterion_id: str
    category: str
    graph_revision: str
    saved_at: str
    facilities: list[Facility]
    baseline_rows: list[AccessRow]
    rows: list[AccessRow]
    closed_way_ids: list[int]
    comparison: RouteComparison
    model_revision: str = REGIONAL_ROAD_REVISION
    mode: str = "car"
    unit: str = "minutes"
    qualification: str = "physical_only"
    fire_profile: FireProfile | None = None
    measurement_definition: MeasurementDefinition = MeasurementDefinition.SINGLE_REFERENCE_POINT

    def __post_init__(self) -> None:
        MeasurementDefinition(self.measurement_definition)

    def receipt(self) -> RegionalMeasurementReceipt:
        return RegionalMeasurementReceipt(
            self.run_id,
            self.region_id,
            self.region_name,
            self.criterion_id,
            self.graph_revision,
            self.saved_at,
            len(self.rows),
            self.comparison.paired_paths + self.comparison.restored,
            len(self.facilities),
            self.mode,
            self.unit,
            self.qualification,
            self.model_revision,
            self.closed_way_ids,
            self.measurement_definition,
        )

    def view(self) -> RegionalRunView:
        return RegionalRunView(
            self.run_id,
            self.region_id,
            self.region_name,
            self.criterion_id,
            self.category,
            self.graph_revision,
            self.saved_at,
            self.closed_way_ids,
            self.comparison,
            self.model_revision,
            self.mode,
            self.unit,
            self.qualification,
            self.fire_profile,
            len(self.rows),
            self.comparison.paired_paths + self.comparison.lost,
            self.comparison.paired_paths + self.comparison.restored,
            len(self.facilities),
            self.measurement_definition,
        )


class RegionalMeasurementRepository(Protocol):
    def origins(self, region_id: str) -> list[Origin]: ...
    def walking_origins(self, revision: str) -> list[Origin]: ...
    def save(self, result: RegionalMeasurement) -> None: ...
    def latest(self, region_id: str, criterion_id: str) -> RegionalMeasurement | None: ...
    def latest_head(self, region_id: str, criterion_id: str) -> RegionalMeasurementHead | None: ...
    def latest_receipt(
        self, region_id: str, criterion_id: str
    ) -> RegionalMeasurementReceipt | None: ...
    def get(self, run_id: str) -> RegionalMeasurement | None: ...


class RegionalMeasurements:
    def __init__(
        self,
        catalog: RegionalCatalogQueries,
        repository: RegionalMeasurementRepository,
        routing: NormativeRouting | None,
        clock: Callable[[], datetime],
        walking: RegionalWalkingModels | None = None,
        fire: NormativeFireRouting | None = None,
        views: RegionalViewRepository | None = None,
    ) -> None:
        self.catalog = catalog
        self.repository = repository
        self.routing = routing
        self.clock = clock
        self.walking = walking
        self.fire = fire
        self.views = views

    def latest(self, region_id: str, criterion_id: str) -> RegionalMeasurement | None:
        self.catalog.scope(region_id, criterion_id)
        return self.repository.latest(region_id, criterion_id)

    def latest_receipt(
        self, region_id: str, criterion_id: str
    ) -> RegionalMeasurementReceipt | None:
        self.catalog.scope(region_id, criterion_id)
        return self.repository.latest_receipt(region_id, criterion_id)

    def calculate(
        self,
        region_id: str,
        criterion_id: str,
        closed_way_ids: list[int],
        fire_profile: FireProfile | None = None,
    ) -> RegionalMeasurement:
        if (
            len(closed_way_ids) > 20
            or len(set(closed_way_ids)) != len(closed_way_ids)
            or any(type(value) is not int or value <= 0 for value in closed_way_ids)
        ):
            raise InvalidQuery("Select up to 20 unique positive road way IDs")
        model = regional_model(
            criterion_id, region_id, self.routing, self.walking, self.fire, fire_profile
        )
        routing = model.routing
        catalog = self.catalog.catalog(region_id, criterion_id, cross_region=model.mode == "car")
        if not catalog.facilities:
            raise DataUnavailable("No regional candidate objects have been imported")
        origins = (
            self.repository.walking_origins(routing.revision)
            if model.mode == "walk"
            else self.repository.origins(region_id)
        )
        if not origins:
            raise DataUnavailable("No reference origins exist for the selected region")
        if routing.missing_ways(closed_way_ids):
            raise InvalidQuery("Unknown road way in the regional closure scenario")

        def evaluate(closed: list[int]) -> list[AccessRow]:
            rows = routing.evaluate(
                origins, catalog.facilities, 1 if model.mode == "walk" else 0, closed
            )
            return [physical_row(row, criterion_id, model.unit) for row in rows]

        baseline = evaluate([])
        scenario = evaluate(closed_way_ids) if closed_way_ids else baseline
        if not any(
            (row.distance_metres if model.unit == "metres" else row.minutes) is not None
            for row in baseline
        ):
            raise DataUnavailable("No candidate object can be reached in the current road model")
        result = RegionalMeasurement(
            uuid4().hex,
            region_id,
            catalog.region_name,
            criterion_id,
            catalog.category,
            routing.revision,
            self.clock().isoformat(),
            catalog.facilities,
            baseline,
            scenario,
            list(closed_way_ids),
            compare_routes(baseline, scenario, model.unit),
            model_revision=model.revision,
            mode=model.mode,
            unit=model.unit,
            fire_profile=fire_profile,
            measurement_definition=model.measurement_definition,
        )
        self.repository.save(result)
        return result

    def route(self, run_id: str, origin_id: str, stage: RouteStage) -> NormativeRoute:
        if self.views is not None:
            return RegionalRouteQueries(self.views, self.routing, self.walking, self.fire).route(
                run_id, origin_id, stage
            )
        result = self.repository.get(run_id)
        if result is None:
            raise InvalidQuery("Unknown regional measurement")
        rows = result.baseline_rows if stage == "baseline" else result.rows
        row = next((row for row in rows if row.id == origin_id), None)
        if row is None:
            raise InvalidQuery("Unknown regional measurement origin")
        facility = next((f for f in result.facilities if f.id == row.facility_id), None)
        return trace_regional_route(
            result.view(),
            RegionalPointDetail(row, facility),
            stage,
            self.routing,
            self.walking,
            self.fire,
        )


def physical_row(row: AccessRow, criterion_id: str, unit: str) -> AccessRow:
    reasons: list[Uncertainty] = list(row.uncertainty) + [
        "facility_profile_unconfirmed",
        "inventory_incomplete",
        "qualification_unconfirmed",
    ]
    if (
        row.routing_node is None
        or row.routing_node < 0
        or row.approach_metres is None
        or not 0 <= row.approach_metres <= (50 if unit == "metres" else 5000)
    ):
        reasons.append("origin_unattached")
    elif (row.distance_metres if unit == "metres" else row.minutes) is None:
        reasons.append("path_unconfirmed")
    return replace(
        row,
        state="unknown",
        excess_minutes=None,
        threshold_minutes=None,
        population=None if unit == "metres" or criterion_id in {"N01", "N02"} else row.population,
        uncertainty=tuple(dict.fromkeys(reasons)),
    )
