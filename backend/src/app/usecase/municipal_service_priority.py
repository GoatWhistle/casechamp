from dataclasses import dataclass

from app.domain.normative.scenario_index import scenario_policy
from app.usecase.municipal_service_models import MunicipalNormativeValue


@dataclass(frozen=True, slots=True)
class MunicipalServicePriority:
    criterion_id: str
    threshold: float
    unit: str
    status: str = 'unavailable'
    reference_points: int = 0
    measured_points: int = 0
    confirmed_deficit_points: int = 0
    unresolved_points: int = 0
    confirmed_deficit_percent: float | None = None
    possible_deficit_percent: float | None = None
    origin_kind: str | None = None
    definition_sha256: str | None = None
    model_revision: str | None = None


def service_priority(criterion_id: str, rows: list[MunicipalNormativeValue]) -> MunicipalServicePriority:
    policy = scenario_policy(criterion_id)
    threshold = policy.thresholds[0]
    unavailable = MunicipalServicePriority(criterion_id, threshold, policy.unit)
    row = next((item for item in rows if item.criterion_id == criterion_id), None)
    if row is None or row.status != 'available' or row.definition_sha256 != policy.definition_sha256:
        return unavailable
    value = next((item for item in row.values if item.threshold == threshold), None)
    if (value is None or value.reference_points <= 0 or value.measured_points <= 0
            or not 0 <= value.within_points <= value.measured_points <= value.reference_points
            or value.unresolved_points != value.reference_points - value.measured_points):
        return unavailable
    confirmed = value.measured_points - value.within_points
    return MunicipalServicePriority(
        criterion_id, threshold, policy.unit, 'available', value.reference_points,
        value.measured_points, confirmed, value.unresolved_points,
        100 * confirmed / value.reference_points,
        100 * (confirmed + value.unresolved_points) / value.reference_points,
        row.origin_kind, row.definition_sha256, row.model_revision,
    )
