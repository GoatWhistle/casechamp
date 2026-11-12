from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import datetime
from typing import Protocol

from app.domain.errors import InvalidQuery
from app.domain.normative.index import IndexBasis, IndexValue, index_weighting
from app.domain.normative.measurement_definition import MeasurementDefinition
from app.usecase.normative.indices import RegionalIndex, index_status
from app.usecase.normative.route import RouteStage
from app.usecase.normative.scenario_indices import ScenarioIndexRepository


@dataclass(frozen=True, slots=True)
class IndexSummary:
    region_id: str
    criterion_id: str
    run_id: str
    measured_at: str
    definition_sha256: str
    unit: str
    weighting: str
    threshold_min: float
    threshold_max: float
    baseline_min: float | None
    baseline_max: float | None
    scenario_min: float | None
    scenario_max: float | None
    reference_points: int
    measured_points: int
    publication_version: int
    index: RegionalIndex | None = None


@dataclass(frozen=True, slots=True)
class IndexMapInput:
    region_id: str
    region_name: str
    basis: IndexBasis | None
    run_id: str | None
    summary: IndexSummary | None
    measurement_definition: MeasurementDefinition = MeasurementDefinition.SINGLE_REFERENCE_POINT


@dataclass(frozen=True, slots=True)
class IndexMapRegion:
    region_id: str
    region_name: str
    value_min: float | None
    value_max: float | None
    weighting: str
    status: str
    run_id: str | None
    measured_at: str | None
    threshold_min: float | None
    threshold_max: float | None
    unit: str | None
    reference_points: int | None
    measured_points: int | None
    legal_compliance_confirmed: bool = False


class IndexMapRepository(Protocol):
    def inputs(self, criterion_id: str) -> list[IndexMapInput]: ...
    def save(self, summary: IndexSummary) -> None: ...


class IndexMapQueries:
    def __init__(
        self,
        repository: IndexMapRepository,
        clock: Callable[[], datetime],
        models: ScenarioIndexRepository | None = None,
    ) -> None:
        self.repository = repository
        self.clock = clock
        self.models = models

    def publish(self, index: RegionalIndex) -> bool:
        if (
            index.basis is None
            or index.status != "ready"
            or index.measurement_definition != index.basis.required_measurement_definition
            or not index.baseline
            or not index.scenario
            or index.run_id is None
            or index.measured_at is None
        ):
            return False
        weighting = index_weighting(index.criterion_id)
        before = value_range(index.baseline, weighting)
        after = value_range(index.scenario, weighting)
        summary = IndexSummary(
            index.region_id,
            index.criterion_id,
            index.run_id,
            index.measured_at,
            index.basis.definition_sha256,
            index.basis.unit,
            weighting,
            min(index.basis.thresholds),
            max(index.basis.thresholds),
            *before,
            *after,
            index.scenario[0].reference_points,
            index.scenario[0].measured_points,
            int(self.clock().timestamp() * 1000000),
            index,
        )
        self.repository.save(summary)
        return True

    def regions(self, criterion_id: str, stage: RouteStage = "scenario") -> list[IndexMapRegion]:
        if criterion_id not in {f"N{i:02}" for i in range(1, 10)}:
            raise InvalidQuery("Unknown service index")
        result = []
        for row in self.repository.inputs(criterion_id):
            summary = row.summary
            status = missing_status(row)
            if status is None and summary is not None:
                low = summary.baseline_min if stage == "baseline" else summary.scenario_min
                high = summary.baseline_max if stage == "baseline" else summary.scenario_max
                result.append(
                    IndexMapRegion(
                        row.region_id,
                        row.region_name,
                        low,
                        high,
                        summary.weighting,
                        "ready" if low is not None else "population_unknown",
                        summary.run_id,
                        summary.measured_at,
                        summary.threshold_min,
                        summary.threshold_max,
                        summary.unit,
                        summary.reference_points,
                        summary.measured_points,
                    )
                )
            else:
                result.append(
                    IndexMapRegion(
                        row.region_id,
                        row.region_name,
                        None,
                        None,
                        index_weighting(criterion_id),
                        status or "unpublished",
                        row.run_id,
                        None,
                        None,
                        None,
                        row.basis.unit if row.basis else None,
                        None,
                        None,
                    )
                )
        if self.models is not None:
            models = {row.region_id: row for row in self.models.regions(criterion_id)}
            for i, mapped in enumerate(result):
                model = models.get(mapped.region_id)
                if mapped.value_min is not None or model is None:
                    continue
                values = model.baseline if stage == "baseline" else model.scenario
                low, high = value_range(values, model.policy.weighting)
                result[i] = replace(
                    mapped,
                    value_min=low,
                    value_max=high,
                    weighting=model.policy.weighting,
                    status="scenario_ready" if low is not None else "population_unknown",
                    run_id=model.run_id,
                    measured_at=model.measured_at,
                    threshold_min=min(model.policy.thresholds),
                    threshold_max=max(model.policy.thresholds),
                    unit=model.policy.unit,
                    reference_points=values[0].reference_points,
                    measured_points=values[0].measured_points,
                )
        return result


def missing_status(row: IndexMapInput) -> str | None:
    mode = "walk" if row.basis and row.basis.criterion_id in {"N04", "N09"} else "car"
    if row.basis and row.basis.criterion_id == "N03":
        mode = "emergency_response"
    status = index_status(row.basis, mode if row.run_id else None, row.measurement_definition)
    if status != "ready":
        return status
    if row.basis is None:
        return "basis_missing"
    if (
        row.summary is None
        or row.summary.run_id != row.run_id
        or row.summary.definition_sha256 != row.basis.definition_sha256
        or row.summary.weighting != index_weighting(row.basis.criterion_id)
        or (
            row.summary.index is not None
            and (
                row.summary.index.basis != row.basis
                or row.summary.index.measurement_definition != row.measurement_definition
            )
        )
        or (
            row.summary.index is None
            and row.measurement_definition != MeasurementDefinition.SINGLE_REFERENCE_POINT
        )
    ):
        return "unpublished"
    return None


def value_range(values: list[IndexValue], weighting: str) -> tuple[float | None, float | None]:
    scores = [
        row.population_share_percent if weighting == "population" else row.point_share_percent
        for row in values
    ]
    if any(value is None for value in scores):
        return None, None
    numeric = [value for value in scores if value is not None]
    return (min(numeric), max(numeric)) if numeric else (None, None)
