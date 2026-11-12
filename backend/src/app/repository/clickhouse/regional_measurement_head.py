from app.domain.normative.measurement_definition import MeasurementDefinition
from app.repository.clickhouse.client import ClickHouseReader
from app.usecase.normative.regional_receipt import RegionalMeasurementHead


def latest_measurement_head(
    reader: ClickHouseReader, table: str, region_id: str, criterion_id: str
) -> RegionalMeasurementHead | None:
    rows = reader.rows(
        f"SELECT id,saved_at,measurement_definition FROM {table} "
        "WHERE region_id={region:String} AND criterion_id={criterion:String} "
        "ORDER BY saved_at DESC,id DESC LIMIT 1",
        {"region": region_id, "criterion": criterion_id},
    )
    if not rows:
        return None
    row = rows[0]
    return RegionalMeasurementHead(
        row["id"], row["saved_at"], MeasurementDefinition(row["measurement_definition"])
    )
