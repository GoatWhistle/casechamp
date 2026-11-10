from app.domain.errors import DataUnavailable
from app.repository.clickhouse.client import ClickHouseReader
from app.usecase.accessibility import (
    AccessibilityComparison,
    AccessibilityRow,
    AccessibilityRun,
    FrequencyCoverage,
)

RUN_SQL = (
    "SELECT run_id,created_at,model_version,source_model,source_artifact,normalization,"
    "normalization_kind,regions,markets,point_count,frequency_status,assumptions,graph_revision "
    "FROM plexus_accessibility.runs ORDER BY created_at DESC,run_id DESC LIMIT 1"
)
ROWS_SQL = (
    "SELECT season,half_life,previous,potential,delta,without_air,without_rail,without_water,"
    "population,population_coverage FROM plexus_accessibility.results "
    "WHERE run_id={run:String} AND region_id={region:String} AND half_life={half:UInt8} "
    "ORDER BY season"
)
FREQUENCIES_SQL = (
    "SELECT season,mode,source,total,known FROM plexus_accessibility.frequencies "
    "WHERE run_id={run:String} ORDER BY season,mode,source"
)


class ClickHouseAccessibilityRepository:
    def __init__(self, reader: ClickHouseReader) -> None:
        self.reader = reader

    def comparison(self, region_id: str, half_life: int) -> AccessibilityComparison:
        runs = self.reader.rows(RUN_SQL, {})
        if len(runs) != 1:
            raise DataUnavailable("No completed accessibility comparison")
        record = dict(runs[0])
        revision = record.pop("graph_revision")
        record["assumptions"] = tuple(record["assumptions"])
        run = AccessibilityRun(**record)
        current = self.reader.rows(
            "SELECT value FROM plexus_atlas.atlas_metadata WHERE key='graph_revision'", {}
        )
        versions = self.reader.rows(
            "SELECT DISTINCT model_version,artifact_version FROM plexus_atlas.atlas_indices", {}
        )
        source_current = (
            len(current) == 1
            and current[0]["value"] == revision
            and len(versions) == 1
            and versions[0]["model_version"] == run.source_model
            and versions[0]["artifact_version"] == run.source_artifact
        )
        rows = self.reader.rows(
            ROWS_SQL, {"run": run.run_id, "region": region_id, "half": half_life}
        )
        frequencies = self.reader.rows(FREQUENCIES_SQL, {"run": run.run_id})
        return AccessibilityComparison(
            region_id,
            source_current,
            run,
            tuple(AccessibilityRow(**row) for row in rows),
            tuple(FrequencyCoverage(**row) for row in frequencies),
        )
