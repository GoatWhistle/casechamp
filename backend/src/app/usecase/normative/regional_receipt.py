from dataclasses import dataclass

from app.domain.normative.measurement_definition import MeasurementDefinition


@dataclass(frozen=True, slots=True)
class RegionalMeasurementHead:
    run_id: str
    saved_at: str
    measurement_definition: MeasurementDefinition


@dataclass(frozen=True, slots=True)
class RegionalMeasurementReceipt:
    run_id: str
    region_id: str
    region_name: str
    criterion_id: str
    graph_revision: str
    saved_at: str
    origins: int
    measured_paths: int
    facilities: int
    mode: str
    unit: str
    qualification: str
    model_revision: str
    closed_way_ids: list[int]
    measurement_definition: MeasurementDefinition = MeasurementDefinition.SINGLE_REFERENCE_POINT
