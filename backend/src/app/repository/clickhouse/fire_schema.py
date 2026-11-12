import pyarrow as pa

from app.repository.clickhouse.transport_schema import TRANSPORT_FACT_FIELDS

FIRE_FACT_FIELDS = [
    *TRANSPORT_FACT_FIELDS,
    ("settlement_type_verified", pa.bool_()),
    ("settlement_type", pa.string()),
    ("speed_verified", pa.bool_()),
    ("speed_kmh", pa.float64()),
    ("speed_source_url", pa.string()),
    ("profile_assumption", pa.string()),
    ("adverse_conditions_verified", pa.bool_()),
    ("vehicle_access_verified", pa.bool_()),
    ("directionality_verified", pa.bool_()),
    ("operational_readiness_verified", pa.bool_()),
    ("destination_objects_verified", pa.bool_()),
    ("population_scope", pa.string()),
    ("population_partition_verified", pa.bool_()),
    ("measurement_definition_verified", pa.bool_()),
    ("measurement_definition", pa.string()),
    ("method_source_url", pa.string()),
    ("method_currentness_verified", pa.bool_()),
    ("method_edition_date", pa.string()),
]
