from app.domain.normative.index import IndexBasis
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.index_basis_record import basis_from_record


class ClickHouseIndexBasisRepository:
    table = "plexus_normative.index_bases"

    def __init__(self, reader: ClickHouseReader) -> None:
        self.reader = reader

    def region_exists(self, region_id: str) -> bool:
        return bool(
            self.reader.rows(
                "SELECT id FROM plexus_normative.inventory_regions FINAL WHERE id={region:String} LIMIT 1",
                {"region": region_id},
            )
        )

    def basis(self, region_id: str, criterion_id: str) -> IndexBasis | None:
        rows = self.reader.rows(
            "SELECT criterion_id,region_id,act,clause,edition_date,source_url,unit,thresholds,definition_sha256,currentness,required_mode,regulation,review,intervals,required_measurement_definition "
            f"FROM {self.table} FINAL "
            "WHERE criterion_id={criterion:String} "
            "AND region_id IN ('RU',{region:String}) ORDER BY region_id!='RU' DESC LIMIT 1",
            {"region": region_id, "criterion": criterion_id},
        )
        if not rows:
            return None
        return basis_from_record(rows[0])
