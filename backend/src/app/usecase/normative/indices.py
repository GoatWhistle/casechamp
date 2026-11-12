from dataclasses import dataclass, replace
from typing import Protocol

from app.domain.errors import DataUnavailable, InvalidQuery
from app.domain.normative.index import IndexBasis, IndexValue, index_values, index_weighting
from app.domain.normative.measurement_definition import MeasurementDefinition
from app.domain.normative.scenario_index import ScenarioIndex
from app.usecase.normative.regional_measurements import RegionalMeasurementRepository
from app.usecase.normative.scenario_indices import ScenarioIndexRepository


class IndexBasisRepository(Protocol):
    def region_exists(self, region_id: str) -> bool: ...
    def basis(self, region_id: str, criterion_id: str) -> IndexBasis | None: ...


@dataclass(frozen=True, slots=True)
class RegionalIndex:
    region_id: str
    criterion_id: str
    run_id: str | None
    measured_at: str | None
    basis: IndexBasis | None
    baseline: list[IndexValue]
    scenario: list[IndexValue]
    qualification: str = "conditional_known_objects"
    legal_compliance_confirmed: bool = False
    status: str = "ready"
    weighting: str = "reference_points"
    measurement_definition: MeasurementDefinition = MeasurementDefinition.SINGLE_REFERENCE_POINT
    model_index: ScenarioIndex | None = None


class RegionalIndexCache(Protocol):
    def latest(
        self, region_id: str, criterion_id: str, basis: IndexBasis
    ) -> RegionalIndex | None: ...


class RegionalIndices:
    def __init__(
        self,
        bases: IndexBasisRepository,
        measurements: RegionalMeasurementRepository,
        cache: RegionalIndexCache | None = None,
        models: ScenarioIndexRepository | None = None,
    ) -> None:
        self.bases = bases
        self.measurements = measurements
        self.cache = cache
        self.models = models

    def latest(self, region_id: str, criterion_id: str) -> RegionalIndex:
        index = self.normative_index(region_id, criterion_id)
        if (not index.scenario or criterion_id == "N03") and self.models is not None:
            return replace(index, model_index=self.models.latest(region_id, criterion_id))
        return index

    def normative_index(self, region_id: str, criterion_id: str) -> RegionalIndex:
        if criterion_id not in {f"N{i:02}" for i in range(1, 10)}:
            raise InvalidQuery("Unknown service index")
        if not self.bases.region_exists(region_id):
            raise InvalidQuery("Unknown service index region")
        basis = self.bases.basis(region_id, criterion_id)
        if (
            basis is None
            or basis.regulation != "threshold"
            or basis.required_mode == "pedestrian_transit"
        ):
            return RegionalIndex(
                region_id,
                criterion_id,
                None,
                None,
                basis,
                [],
                [],
                status=index_status(basis, None),
                weighting=index_weighting(criterion_id),
            )
        if self.cache is not None:
            cached = self.cache.latest(region_id, criterion_id, basis)
            if (
                cached is not None
                and cached.measurement_definition == basis.required_measurement_definition
            ):
                return cached
        head = self.measurements.latest_head(region_id, criterion_id)
        if head is None or head.measurement_definition != basis.required_measurement_definition:
            return RegionalIndex(
                region_id,
                criterion_id,
                head.run_id if head else None,
                head.saved_at if head else None,
                basis,
                [],
                [],
                status="measurement_incompatible" if head else "measurement_missing",
                weighting=index_weighting(criterion_id),
                measurement_definition=head.measurement_definition
                if head
                else MeasurementDefinition.SINGLE_REFERENCE_POINT,
            )
        measurement = self.measurements.get(head.run_id)
        if measurement is not None and measurement.run_id != head.run_id:
            raise DataUnavailable("The regional snapshot differs from its published identifier")
        status = index_status(
            basis,
            measurement.mode if measurement else None,
            measurement.measurement_definition if measurement else None,
        )
        if status != "ready" or measurement is None or basis is None:
            return RegionalIndex(
                region_id,
                criterion_id,
                measurement.run_id if measurement else None,
                measurement.saved_at if measurement else None,
                basis,
                [],
                [],
                status=status,
                weighting=index_weighting(criterion_id),
                measurement_definition=measurement.measurement_definition
                if measurement
                else MeasurementDefinition.SINGLE_REFERENCE_POINT,
            )
        if basis.unit != measurement.unit:
            raise InvalidQuery("Index basis and physical measurement units differ")
        return RegionalIndex(
            region_id,
            criterion_id,
            measurement.run_id,
            measurement.saved_at,
            basis,
            index_values(measurement.baseline_rows, basis, measurement.measurement_definition),
            index_values(measurement.rows, basis, measurement.measurement_definition),
            weighting=index_weighting(criterion_id),
            measurement_definition=measurement.measurement_definition,
        )


def index_status(
    basis: IndexBasis | None,
    mode: str | None,
    measurement_definition: MeasurementDefinition
    | None = MeasurementDefinition.SINGLE_REFERENCE_POINT,
) -> str:
    if basis is None:
        return "basis_missing"
    if basis.regulation in {"not_regulated", "local_selection_required"}:
        return basis.regulation
    if basis.required_mode == "pedestrian_transit":
        return "model_unavailable"
    if mode is None:
        return "measurement_missing"
    if basis.required_mode != mode:
        return "model_unavailable"
    if basis.required_measurement_definition != measurement_definition:
        return "measurement_incompatible"
    return "ready"
