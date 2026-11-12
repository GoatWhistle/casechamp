import json
from typing import Any

from app.domain.normative.index import IndexBasis, IndexBasisReview, IndexThresholdInterval
from app.domain.normative.measurement_definition import MeasurementDefinition


def basis_from_record(row: dict[str, Any]) -> IndexBasis:
    record = dict(row)
    review = record.pop("review", None)
    intervals = record.pop("intervals", ())
    if isinstance(review, str):
        review = json.loads(review) if review else None
    if isinstance(intervals, str):
        intervals = json.loads(intervals)
    record["required_measurement_definition"] = MeasurementDefinition(
        record.get("required_measurement_definition", MeasurementDefinition.SINGLE_REFERENCE_POINT)
    )
    return IndexBasis(
        **{**record, "thresholds": tuple(record["thresholds"])},
        review=IndexBasisReview(**review) if review else None,
        intervals=tuple(IndexThresholdInterval(**item) for item in intervals),
    )
