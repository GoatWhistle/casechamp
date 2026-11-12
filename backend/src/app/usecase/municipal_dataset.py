import json
from dataclasses import asdict, dataclass
from hashlib import sha256
from typing import Protocol

from app.domain.municipal_metrics import municipal_contains
from app.domain.normative.index import index_weighting, reference_index_values
from app.domain.normative.measurement_definition import MeasurementDefinition
from app.domain.normative.model import AccessRow
from app.domain.normative.scenario_index import scenario_policy
from app.usecase.municipal_service_models import MunicipalNormativeValue
from app.usecase.municipalities import Municipality


@dataclass(frozen=True, slots=True)
class MunicipalSnapshotSource:
    region_id: str
    criterion_id: str
    run_id: str
    stage: str
    measured_at: str
    graph_revision: str
    model_revision: str
    qualification: str
    measurement_definition: str
    metadata_json: str


def municipal_boundary_digest(municipalities: list[Municipality]) -> str:
    return sha256(
        json.dumps(
            [asdict(item) for item in sorted(municipalities, key=lambda item: item.id)],
            sort_keys=True,
            ensure_ascii=False,
            allow_nan=False,
        ).encode()
    ).hexdigest()


class MunicipalDataset(Protocol):
    def boundaries(self, municipalities: list[Municipality]) -> str: ...
    def find_boundaries(self, region_id: str) -> str | None: ...
    def find_run(
        self, region_id: str, criterion_id: str, run_id: str, stage: str
    ) -> str | None: ...
    def snapshot(self, source: MunicipalSnapshotSource, rows: list[AccessRow]) -> str: ...
    def rows(self, source_sha256: str) -> list[AccessRow]: ...
    def source(self, source_sha256: str) -> MunicipalSnapshotSource: ...
    def aggregate(
        self,
        source_sha256: str,
        municipality: Municipality,
        value: MunicipalNormativeValue,
        point_ids: list[str],
        source_key: str | None = None,
        boundary_snapshot_sha256: str | None = None,
    ) -> None: ...
    def lookup(
        self, municipality: Municipality, criterion_id: str, source_key: str
    ) -> MunicipalNormativeValue | None: ...
    def existing(
        self,
        source_sha256: str,
        municipality: Municipality,
        criterion_id: str,
        boundary_snapshot_sha256: str | None = None,
    ) -> MunicipalNormativeValue | None: ...


def snapshot_digest(source: MunicipalSnapshotSource, rows: list[AccessRow]) -> str:
    if len({row.id for row in rows}) != len(rows):
        raise ValueError("Snapshot point identifiers must be unique")
    digest = sha256(json.dumps(asdict(source), sort_keys=True, allow_nan=False).encode())
    for row in sorted(rows, key=lambda item: item.id):
        digest.update(b"\n" + json.dumps(asdict(row), sort_keys=True, allow_nan=False).encode())
    return digest.hexdigest()


def aggregate_snapshot(
    source: MunicipalSnapshotSource,
    rows: list[AccessRow],
    municipality: Municipality,
    preassigned: bool = False,
) -> tuple[MunicipalNormativeValue, list[str]]:
    if source.region_id != municipality.region_id:
        raise ValueError("Municipal and source region identifiers differ")
    policy = scenario_policy(source.criterion_id)
    metadata = json.loads(source.metadata_json)
    if preassigned:
        selected = rows
    else:
        vertices = [
            point for polygon in municipality.coordinates for ring in polygon for point in ring
        ]
        west, east = min(p[0] for p in vertices), max(p[0] for p in vertices)
        south, north = min(p[1] for p in vertices), max(p[1] for p in vertices)
        selected = [
            row
            for row in rows
            if row.longitude is not None
            and row.latitude is not None
            and south <= row.latitude <= north
            and any(west <= row.longitude + shift <= east for shift in (-360, 0, 360))
            and municipal_contains(row.longitude, row.latitude, municipality.coordinates)
        ]
    identifiers = [row.id for row in selected]
    entry = MunicipalNormativeValue(
        source.criterion_id,
        unit=policy.unit,
        mode=policy.mode,
        thresholds=policy.thresholds,
        definition_sha256=policy.definition_sha256,
        reference_points=len(selected),
        model_revision=source.model_revision,
        qualification=source.qualification,
        origin_kind=metadata.get(
            "origin_kind",
            "residential_reference_points"
            if policy.mode == "walk"
            else "settlement_reference_points",
        ),
        source_urls=tuple(metadata.get("source_urls", [])),
    )
    if metadata.get("unavailable_reason"):
        return MunicipalNormativeValue(
            **{**asdict(entry), "reason": metadata["unavailable_reason"]}
        ), identifiers
    if (
        source.measurement_definition != MeasurementDefinition.SINGLE_REFERENCE_POINT
        or metadata.get("mode") != policy.mode
        or metadata.get("unit") != policy.unit
        or (
            source.criterion_id == "N03"
            and metadata.get("fire_profile", {}).get("speed_kmh") != policy.fire_speed_kmh
        )
    ):
        return MunicipalNormativeValue(
            **{**asdict(entry), "reason": "municipal_measurement_policy_mismatch"}
        ), identifiers
    values = reference_index_values(selected, policy.unit, policy.thresholds)
    costs = [row.distance_metres if policy.unit == "metres" else row.minutes for row in selected]
    finite = [cost for cost in costs if cost is not None]
    primary = (
        values[0].population_share_percent
        if index_weighting(source.criterion_id) == "population"
        else values[0].point_share_percent
    )
    return MunicipalNormativeValue(
        **{
            **asdict(entry),
            "value": primary if finite else None,
            "status": "available" if finite and primary is not None else "unavailable",
            "reason": "conditional_known_objects"
            if finite and primary is not None
            else "municipal_population_missing"
            if finite
            else "municipal_routes_unresolved",
            "values": tuple(values),
            "mean_travel": sum(finite) / len(finite) if finite else None,
            "measured_points": len(finite),
            "facilities": int(metadata.get("facilities", 0)),
        }
    ), identifiers


def persist_aggregation(
    dataset: MunicipalDataset,
    source_sha256: str,
    municipality: Municipality,
    source_key: str | None = None,
) -> MunicipalNormativeValue:
    source = dataset.source(source_sha256)
    cached = dataset.existing(source_sha256, municipality, source.criterion_id)
    if cached is not None:
        return cached
    value, identifiers = aggregate_snapshot(source, dataset.rows(source_sha256), municipality)
    dataset.aggregate(source_sha256, municipality, value, identifiers, source_key)
    return value
