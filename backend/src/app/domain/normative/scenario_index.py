from dataclasses import dataclass
from hashlib import sha256

from app.domain.normative.index import IndexValue, index_weighting
from app.domain.normative.measurement_definition import MeasurementDefinition

SCENARIO_THRESHOLDS = {
    "N01": (60.0,),
    "N02": (120.0,),
    "N03": (10.0, 20.0),
    "N04": (500.0, 800.0, 1000.0),
    "N05": (60.0,),
    "N06": (60.0,),
    "N07": (40.0, 60.0),
    "N08": (60.0,),
    "N09": (500.0, 800.0),
}


@dataclass(frozen=True, slots=True)
class ScenarioIndexPolicy:
    criterion_id: str
    thresholds: tuple[float, ...]
    unit: str
    mode: str
    weighting: str
    definition_sha256: str
    fire_speed_kmh: float | None = None


def scenario_policy(criterion_id: str) -> ScenarioIndexPolicy:
    thresholds = SCENARIO_THRESHOLDS[criterion_id]
    mode = (
        "walk"
        if criterion_id in {"N04", "N09"}
        else "emergency_response"
        if criterion_id == "N03"
        else "car"
    )
    unit = "metres" if mode == "walk" else "minutes"
    speed = 40.0 if criterion_id == "N03" else None
    weighting = index_weighting(criterion_id)
    digest = sha256(
        repr(
            ("scenario-reference-v2", criterion_id, thresholds, unit, mode, weighting, speed)
        ).encode()
    ).hexdigest()
    return ScenarioIndexPolicy(criterion_id, thresholds, unit, mode, weighting, digest, speed)


@dataclass(frozen=True, slots=True)
class ScenarioIndex:
    region_id: str
    criterion_id: str
    run_id: str
    measured_at: str
    policy: ScenarioIndexPolicy
    baseline: list[IndexValue]
    scenario: list[IndexValue]
    measurement_definition: MeasurementDefinition = MeasurementDefinition.SINGLE_REFERENCE_POINT
    legal_compliance_confirmed: bool = False
