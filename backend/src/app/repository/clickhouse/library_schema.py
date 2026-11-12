import pyarrow as pa

from app.repository.clickhouse.transport_schema import TRANSPORT_FACT_FIELDS

LIBRARY_FACT_FIELDS = [
    *TRANSPORT_FACT_FIELDS,
    ("municipality_type", pa.string()),
    ("municipality_code", pa.string()),
]
