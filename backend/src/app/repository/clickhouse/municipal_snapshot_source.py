import json
from dataclasses import asdict
from hashlib import sha256

from app.domain.normative.model import AccessRow
from app.repository.clickhouse.regional_measurements import ClickHouseRegionalMeasurementRepository
from app.usecase.municipal_dataset import MunicipalSnapshotSource


class ClickHouseMunicipalSnapshotSource:
    def __init__(self, measurements: ClickHouseRegionalMeasurementRepository) -> None:
        self.measurements = measurements

    def latest(
        self, region_id: str, criterion_id: str, stage: str
    ) -> tuple[MunicipalSnapshotSource, list[AccessRow]] | None:
        measurement = self.measurements.latest(region_id, criterion_id)
        if measurement is None:
            return None
        metadata = {
            "catalog_fingerprint": sha256(
                json.dumps(
                    [asdict(facility) for facility in measurement.facilities],
                    sort_keys=True,
                    allow_nan=False,
                ).encode()
            ).hexdigest(),
            "mode": measurement.mode,
            "unit": measurement.unit,
            "fire_profile": asdict(measurement.fire_profile) if measurement.fire_profile else {},
            "facilities": len(measurement.facilities),
            "source_urls": sorted({facility.source_url for facility in measurement.facilities}),
            "facility_sources": [asdict(facility) for facility in measurement.facilities],
            "closed_way_ids": measurement.closed_way_ids if stage == "scenario" else [],
            "origin_kind": "residential_reference_points"
            if measurement.mode == "walk"
            else "settlement_reference_points",
        }
        source = MunicipalSnapshotSource(
            region_id,
            criterion_id,
            measurement.run_id,
            stage,
            measurement.saved_at,
            measurement.graph_revision,
            measurement.model_revision,
            measurement.qualification,
            measurement.measurement_definition,
            json.dumps(metadata, sort_keys=True, allow_nan=False),
        )
        return source, measurement.rows if stage == "scenario" else measurement.baseline_rows
