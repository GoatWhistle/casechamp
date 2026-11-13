import json
from dataclasses import dataclass
from typing import Any

from app.domain.errors import DataUnavailable, InvalidQuery
from app.domain.normative.model import AccessRow, Facility
from app.domain.normative.scenario_index import scenario_policy
from app.usecase.municipal_access import MunicipalAccessQueries
from app.usecase.normative.regional_models import REGIONAL_ROAD_REVISION

SOCIAL_CRITERIA = ("N01", "N02", "N05", "N06", "N07", "N08")


@dataclass(frozen=True)
class MunicipalSocialPoint:
    id: str
    name: str
    latitude: float | None
    longitude: float | None
    before_minutes: float | None
    after_minutes: float | None
    added_minutes: float | None
    before_facility_id: str | None
    after_facility_id: str | None
    after_facility_name: str | None
    route_after_exists: bool | None
    crossed_threshold: bool


@dataclass(frozen=True)
class MunicipalSocialEffect:
    criterion_id: str
    threshold_minutes: float
    status: str = "unavailable"
    reason: str | None = "social_source_unavailable"
    source_sha256: str | None = None
    reference_points: int = 0
    unresolved_points: int = 0
    lost_routes: int = 0
    restored_routes: int = 0
    delayed_points: int = 0
    crossed_threshold_points: int = 0
    before_within: int = 0
    after_within: int = 0
    attached_facilities: int = 0
    unattached_facilities: int = 0
    points: tuple[MunicipalSocialPoint, ...] = ()
    method: str = "directed_loaded_network_fixed_attachments_known_objects_v1"
    legal_compliance_confirmed: bool = False


@dataclass(frozen=True)
class MunicipalSocialSource:
    criterion_id: str
    sha256: str
    graph_revision: str
    rows: list[AccessRow]
    facilities: list[Facility]


class MunicipalSocialSources:
    def __init__(self, access: MunicipalAccessQueries) -> None:
        self.access = access

    def load(self, region_id: str, municipality_id: str, criterion_id: str) -> MunicipalSocialSource:
        municipality = next((item for item in self.access.municipalities.run(region_id).items
                             if item.id == municipality_id), None)
        if municipality is None or criterion_id not in SOCIAL_CRITERIA:
            raise InvalidQuery("Unknown municipal social scenario scope")
        snapshot = self.access.snapshot(municipality, criterion_id)
        if snapshot is None:
            raise DataUnavailable("Published social measurement is unavailable")
        metadata = json.loads(snapshot.source.metadata_json)
        if (snapshot.source.model_revision != REGIONAL_ROAD_REVISION
                or metadata.get("mode") != "car" or metadata.get("unit") != "minutes"
                or metadata.get("closed_way_ids") or metadata.get("unavailable_reason")):
            raise DataUnavailable("A current cross-border social baseline is required")
        facilities = [Facility(**row) for row in metadata.get("facility_sources", [])]
        if not facilities:
            raise DataUnavailable("Saved social facility catalog is unavailable")
        return MunicipalSocialSource(criterion_id, snapshot.sha256, snapshot.source.graph_revision,
                                     self.access.selected_rows(snapshot, municipality), facilities)


def summarize_social(
    source: MunicipalSocialSource,
    points: list[MunicipalSocialPoint],
    attached: int,
) -> MunicipalSocialEffect:
    threshold = scenario_policy(source.criterion_id).thresholds[0]
    ordered = sorted(points, key=lambda point: (
        0 if point.before_minutes is not None and point.route_after_exists is False else 1,
        -(point.added_minutes or 0), point.id,
    ))
    return MunicipalSocialEffect(
        source.criterion_id, threshold, "available", None, source.sha256, len(points),
        sum(point.route_after_exists is None for point in points),
        sum(point.before_minutes is not None and point.route_after_exists is False for point in points),
        sum(point.before_minutes is None and point.after_minutes is not None for point in points),
        sum(point.added_minutes is not None and point.added_minutes > 1e-6 for point in points),
        sum(point.crossed_threshold for point in points),
        sum(point.before_minutes is not None and point.before_minutes <= threshold for point in points),
        sum(point.after_minutes is not None and point.after_minutes <= threshold for point in points),
        attached, len(source.facilities) - attached, tuple(ordered),
    )


def restore_social(record: dict[str, Any]) -> MunicipalSocialEffect:
    return MunicipalSocialEffect(**{**record, "points": tuple(
        MunicipalSocialPoint(**point) for point in record.get("points", [])
    )})
