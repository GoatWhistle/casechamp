from dataclasses import dataclass

from app.domain.municipal_metrics import MunicipalObservation
from app.domain.normative.index import IndexValue
from app.domain.normative.model import Origin
from app.domain.normative.scenario_index import scenario_policy


@dataclass(frozen=True, slots=True)
class MunicipalNormativeValue:
    criterion_id: str
    value: float | None = None
    status: str = "unavailable"
    reason: str | None = "municipal_point_measurements_unavailable"
    basis_kind: str = "scenario_reference"
    qualification: str = "physical_only"
    legal_compliance_confirmed: bool = False
    unit: str | None = None
    mode: str | None = None
    thresholds: tuple[float, ...] = ()
    values: tuple[IndexValue, ...] = ()
    mean_travel: float | None = None
    measured_points: int = 0
    reference_points: int = 0
    facilities: int = 0
    model_revision: str | None = None
    definition_sha256: str | None = None
    source_urls: tuple[str, ...] = ()
    origin_kind: str = "settlement_reference_points"


def merge_municipal_values(
    published: list[MunicipalNormativeValue], live: list[MunicipalNormativeValue]
) -> list[MunicipalNormativeValue]:
    merged = {item.criterion_id: item for item in [*live, *published]}
    return [merged.get(f"N{i:02}", MunicipalNormativeValue(f"N{i:02}")) for i in range(1, 10)]


def municipal_origins(points: list[MunicipalObservation]) -> list[Origin]:
    return [
        Origin(
            point.point_id,
            point.point_id,
            None,
            point.node,
            point.snap_km,
            point.latitude,
            point.longitude,
        )
        for point in points
    ]


def municipal_pending(criterion_id: str) -> MunicipalNormativeValue:
    policy = scenario_policy(criterion_id)
    return MunicipalNormativeValue(
        criterion_id,
        status="pending",
        reason="municipal_calculation_running",
        unit=policy.unit,
        mode=policy.mode,
        thresholds=policy.thresholds,
        definition_sha256=policy.definition_sha256,
    )
