from dataclasses import dataclass
from datetime import date
from math import isfinite

from app.domain.normative.measurement_definition import MeasurementDefinition
from app.domain.normative.model import AccessRow


@dataclass(frozen=True, slots=True)
class IndexBasisReview:
    reviewed_at: str
    as_of: str
    locator: str
    source_url: str
    source_sha256: str
    scope: str


@dataclass(frozen=True, slots=True)
class IndexThresholdInterval:
    minimum: float
    maximum: float
    municipality_type: str
    mode: str
    profile: str


@dataclass(frozen=True, slots=True)
class IndexBasis:
    criterion_id: str
    region_id: str
    act: str
    clause: str
    edition_date: str
    source_url: str
    unit: str
    thresholds: tuple[float, ...]
    definition_sha256: str
    currentness: str
    required_mode: str = "car"
    regulation: str = "threshold"
    review: IndexBasisReview | None = None
    intervals: tuple[IndexThresholdInterval, ...] = ()
    required_measurement_definition: MeasurementDefinition = (
        MeasurementDefinition.SINGLE_REFERENCE_POINT
    )


@dataclass(frozen=True, slots=True)
class IndexValue:
    threshold: float
    reference_points: int
    measured_points: int
    within_points: int
    unresolved_points: int
    point_share_percent: float | None
    population: int | None
    within_population: int | None
    population_share_percent: float | None


def index_values(
    rows: list[AccessRow],
    basis: IndexBasis,
    measurement_definition: MeasurementDefinition = MeasurementDefinition.SINGLE_REFERENCE_POINT,
) -> list[IndexValue]:
    if len({row.id for row in rows}) != len(rows):
        raise ValueError("Index reference points must be unique")
    validate_index_basis(basis)
    if basis.regulation != "threshold":
        return []
    if measurement_definition != basis.required_measurement_definition:
        raise ValueError("Index basis requires a compatible measurement definition")
    return reference_index_values(rows, basis.unit, basis.thresholds)


def reference_index_values(
    rows: list[AccessRow], unit: str, thresholds: tuple[float, ...]
) -> list[IndexValue]:
    if (
        unit not in {"minutes", "metres"}
        or not thresholds
        or any(not isfinite(t) or t <= 0 for t in thresholds)
    ):
        raise ValueError("Reference indices require valid units and thresholds")
    if len({row.id for row in rows}) != len(rows):
        raise ValueError("Index reference points must be unique")
    costs = [row.distance_metres if unit == "metres" else row.minutes for row in rows]
    if any(cost is not None and (not isfinite(cost) or cost < 0) for cost in costs):
        raise ValueError("Index measurements must be finite and nonnegative")
    if any(row.population is not None and row.population < 0 for row in rows):
        raise ValueError("Index population cannot be negative")
    measured = sum(cost is not None for cost in costs)
    population_known = bool(rows) and all(row.population is not None for row in rows)
    population = sum(row.population or 0 for row in rows) if population_known else None
    result = []
    for threshold in thresholds:
        mask = [cost is not None and cost <= threshold for cost in costs]
        within = sum(mask)
        residents = (
            sum((row.population or 0) for row, included in zip(rows, mask, strict=True) if included)
            if population_known
            else None
        )
        result.append(
            IndexValue(
                threshold,
                len(rows),
                measured,
                within,
                len(rows) - measured,
                100 * within / len(rows) if rows else None,
                population,
                residents,
                100 * residents / population if population and residents is not None else None,
            )
        )
    return result


def validate_index_basis(basis: IndexBasis) -> None:
    MeasurementDefinition(basis.required_measurement_definition)
    if (
        basis.required_measurement_definition == MeasurementDefinition.STOP_PAVILION_PARCEL_BOUNDARY
        and (basis.unit != "metres" or basis.required_mode != "walk")
    ):
        raise ValueError("Stop parcel boundary measurements require pedestrian distances")
    if basis.review is not None:
        date.fromisoformat(basis.review.reviewed_at)
        date.fromisoformat(basis.review.as_of)
        if not basis.review.locator:
            raise ValueError("Index review requires a source locator")
    if basis.required_mode not in {
        "car",
        "walk",
        "emergency_response",
        "pedestrian_transit",
        "none",
    }:
        raise ValueError("Unknown index transport mode")
    if basis.review is not None and (
        basis.review.scope not in {"registry_listing", "consolidated_text"}
        or not basis.review.source_url.startswith(("http://", "https://"))
        or len(basis.review.source_sha256) != 64
        or any(c not in "0123456789abcdef" for c in basis.review.source_sha256)
    ):
        raise ValueError("Index review requires a known scope, HTTP source and source SHA256")
    if basis.intervals and basis.regulation != "local_selection_required":
        raise ValueError("Source intervals require an explicit local threshold selection")
    if basis.regulation == "local_selection_required":
        if (
            not basis.intervals
            or basis.thresholds
            or any(
                not isfinite(row.minimum)
                or not isfinite(row.maximum)
                or row.minimum <= 0
                or row.minimum > row.maximum
                or not row.municipality_type
                or row.mode not in {"transport", "pedestrian_or_transport"}
                or not row.profile
                for row in basis.intervals
            )
        ):
            raise ValueError("Local threshold selection requires valid source intervals and scope")
        return
    if basis.regulation == "not_regulated" and not basis.thresholds:
        return
    if (
        basis.regulation != "threshold"
        or not basis.thresholds
        or basis.unit not in {"minutes", "metres"}
        or any(not isfinite(t) or t <= 0 for t in basis.thresholds)
    ):
        raise ValueError("Index basis requires positive finite thresholds and a known unit")


def index_weighting(criterion_id: str) -> str:
    return (
        "population" if criterion_id in {"N03", "N05", "N06", "N07", "N08"} else "reference_points"
    )
