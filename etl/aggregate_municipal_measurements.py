import argparse
import fcntl
import json
import os
from datetime import UTC, datetime
from pathlib import Path

from app.adapter.municipal.assignment import MunicipalSpatialIndex
from app.domain.errors import DataUnavailable
from app.domain.normative.measurement_definition import MeasurementDefinition
from app.domain.normative.scenario_index import scenario_policy
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.municipal_snapshot_source import (
    ClickHouseMunicipalSnapshotSource,
)
from app.repository.clickhouse.municipalities import ClickHouseMunicipalRepository
from app.repository.clickhouse.regional_measurements import (
    ClickHouseRegionalMeasurementRepository,
)
from app.repository.files.municipal_dataset import JsonMunicipalDataset
from app.repository.files.municipal_dataset_export import export_municipal_dataset
from app.usecase.municipal_dataset import MunicipalSnapshotSource, aggregate_snapshot


def atomic_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".part")
    temporary.write_text(
        json.dumps(value, sort_keys=True, ensure_ascii=False, indent=2) + "\n"
    )
    temporary.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--export", type=Path)
    parser.add_argument("--regions", nargs="+")
    parser.add_argument(
        "--criteria",
        nargs="+",
        choices=[f"N{i:02}" for i in range(1, 10)],
        default=[f"N{i:02}" for i in range(1, 10)],
    )
    parser.add_argument("--stage", choices=("baseline", "scenario"), default="scenario")
    parser.add_argument("--stop-file", type=Path)
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    with (args.output / ".export.lock").open("a") as lock:
        try:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise SystemExit(
                "Another municipal dataset export is already running"
            ) from error
        run(args)


def run(args: argparse.Namespace) -> None:
    reader = ClickHouseReader(
        os.environ.get("CLICKHOUSE_URL", "http://127.0.0.1:18123"),
        os.environ.get("CLICKHOUSE_USER", "plexus"),
        os.environ.get("CLICKHOUSE_PASSWORD", ""),
        max_threads=2,
    )
    dataset = JsonMunicipalDataset(args.output)
    measurements = ClickHouseRegionalMeasurementRepository(reader)
    source_reader = ClickHouseMunicipalSnapshotSource(measurements)
    municipality_reader = ClickHouseMunicipalRepository(reader)
    regions = args.regions or [
        str(row["region_id"])
        for row in reader.rows(
            "SELECT DISTINCT region_id FROM plexus_atlas.municipal_boundaries ORDER BY region_id",
            {},
        )
    ]
    records: list[dict[str, object]] = []
    for region in regions:
        municipalities = municipality_reader.boundaries(region)
        boundary_digest = dataset.boundaries(municipalities)
        spatial_index = MunicipalSpatialIndex(municipalities)
        for criterion in args.criteria:
            if args.stop_file and args.stop_file.exists():
                atomic_json(
                    args.output / "batch-progress.json",
                    {"status": "stopped", "records": records},
                )
                return
            try:
                head = measurements.latest_head(region, criterion)
                digest = (
                    dataset.find_run(region, criterion, head.run_id, args.stage)
                    if head
                    else None
                )
                if digest is None:
                    loaded = (
                        source_reader.latest(region, criterion, args.stage)
                        if head
                        else None
                    )
                    if loaded is not None:
                        source, rows = loaded
                    else:
                        policy = scenario_policy(criterion)
                        source = MunicipalSnapshotSource(
                            region,
                            criterion,
                            "missing",
                            args.stage,
                            "",
                            "",
                            "",
                            "unavailable",
                            MeasurementDefinition.SINGLE_REFERENCE_POINT,
                            json.dumps(
                                {
                                    "mode": policy.mode,
                                    "unit": policy.unit,
                                    "unavailable_reason": "regional_point_measurements_unavailable",
                                }
                            ),
                        )
                        rows = []
                    digest = dataset.snapshot(source, rows)
                source = dataset.source(digest)
                pending = [
                    municipality
                    for municipality in municipalities
                    if dataset.existing(digest, municipality, criterion) is None
                ]
                rows = dataset.rows(digest) if pending else []
                assignment = spatial_index.assign(rows)
                available = 0
                for municipality in pending:
                    value, identifiers = aggregate_snapshot(
                        source,
                        assignment.rows[municipality.id],
                        municipality,
                        preassigned=True,
                    )
                    dataset.aggregate(
                        digest,
                        municipality,
                        value,
                        identifiers,
                        boundary_snapshot_sha256=boundary_digest,
                    )
                    available += value.status == "available"
                record = {
                    "region_id": region,
                    "criterion_id": criterion,
                    "status": "complete",
                    "source_sha256": digest,
                    "source_run_id": source.run_id,
                    "municipalities": len(municipalities),
                    "computed": len(pending),
                    "resumed": len(municipalities) - len(pending),
                    "new_available": available,
                    "assignment": {
                        "assigned": assignment.assigned,
                        "ambiguous_excluded": assignment.ambiguous,
                        "outside": assignment.outside,
                        "coordinates_missing": assignment.coordinates_missing,
                    },
                    "boundary_snapshot_sha256": boundary_digest,
                }
            except (DataUnavailable, ValueError, OSError) as error:
                record = {
                    "region_id": region,
                    "criterion_id": criterion,
                    "status": "failed",
                    "error": str(error),
                }
            records.append(record)
            atomic_json(
                args.output / "batch-progress.json",
                {
                    "status": "running",
                    "records": records,
                    "updated_at": datetime.now(UTC).isoformat(),
                },
            )
            print(json.dumps(record, sort_keys=True), flush=True)
    export = export_municipal_dataset(args.output, args.export) if args.export else None
    atomic_json(
        args.output / "batch-progress.json",
        {"status": "complete", "records": records, "export": export},
    )
    if any(record["status"] == "failed" for record in records):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
