from dataclasses import dataclass


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
    data_source: str = "live"
    source_report: str | None = None
    source_report_sha256: str | None = None
    source_checked_at: str | None = None
    detail_available: bool = True
