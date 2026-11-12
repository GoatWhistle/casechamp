import pyarrow as pa

from app.repository.clickhouse.transport_schema import TRANSPORT_FACT_FIELDS

MEDICAL_FACT_FIELDS = [
    *TRANSPORT_FACT_FIELDS,
    ("service", pa.string()),
    ("population_group", pa.string()),
    ("ownership_scope_verified", pa.bool_()),
    ("ownership_applicable", pa.bool_()),
    ("facility_form_verified", pa.bool_()),
    ("adult_profile_verified", pa.bool_()),
    ("catchment_verified", pa.bool_()),
    ("catchment_source_url", pa.string()),
    ("regional_adjustment_verified", pa.bool_()),
    ("regional_adjustment_source_url", pa.string()),
    ("threshold_minutes", pa.float64()),
]
