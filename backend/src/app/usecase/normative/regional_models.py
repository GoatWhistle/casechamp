from dataclasses import dataclass
from typing import Protocol

from app.domain.errors import DataUnavailable, InvalidQuery
from app.domain.normative.fire import FireProfile
from app.domain.normative.measurement_definition import MeasurementDefinition
from app.usecase.normative.interface import NormativeFireRouting, NormativeRouting
from app.usecase.normative.regional_catalog import ROAD_CRITERIA


class RegionalWalkingModels(Protocol):
    def for_region(self, region_id: str) -> NormativeRouting: ...


@dataclass(frozen=True, slots=True)
class RegionalModel:
    routing: NormativeRouting
    mode: str
    unit: str
    revision: str
    measurement_definition: MeasurementDefinition = MeasurementDefinition.SINGLE_REFERENCE_POINT


def regional_model(
    criterion_id: str,
    region_id: str,
    road: NormativeRouting | None,
    walking: RegionalWalkingModels | None,
    fire: NormativeFireRouting | None,
    profile: FireProfile | None,
) -> RegionalModel:
    if criterion_id != "N03" and profile is not None:
        raise InvalidQuery("Fire travel parameters only apply to N03")
    if criterion_id in ROAD_CRITERIA:
        if road is None:
            raise DataUnavailable("Regional road routing is not configured")
        return RegionalModel(road, "car", "minutes", "regional-road-v1")
    if criterion_id in {"N04", "N09"}:
        if walking is None:
            raise DataUnavailable("Regional pedestrian routing is not configured")
        return RegionalModel(walking.for_region(region_id), "walk", "metres", "regional-walk-v2")
    if criterion_id == "N03":
        if profile is None:
            raise InvalidQuery("Specify the fire travel speed and its assumption")
        if fire is None:
            raise DataUnavailable("Regional fire travel routing is not configured")
        return RegionalModel(
            fire.with_profile(profile), "emergency_response", "minutes", "regional-fire-v1"
        )
    raise InvalidQuery("Unknown regional measurement model")
