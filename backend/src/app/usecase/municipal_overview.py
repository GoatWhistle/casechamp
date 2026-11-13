from collections.abc import Callable
from dataclasses import dataclass

from app.domain.errors import InvalidQuery
from app.domain.municipal_metrics import MunicipalMetric, aggregate_metric, municipal_points
from app.usecase.municipal_indices import MunicipalIndexRepository
from app.usecase.municipal_service_models import MunicipalNormativeValue
from app.usecase.municipal_service_priority import MunicipalServicePriority, service_priority
from app.usecase.municipalities import Municipality, MunicipalityQueries


@dataclass(frozen=True, slots=True)
class MunicipalOverviewItem:
    municipality_id: str
    name: str
    connectivity: MunicipalMetric
    difference_from_region: float | None
    reasons: list[str]
    service: MunicipalServicePriority | None = None


@dataclass(frozen=True, slots=True)
class MunicipalOverview:
    region_id: str
    items: list[MunicipalOverviewItem]
    region_connectivity: MunicipalMetric
    model_version: str | None
    artifact_version: str | None
    source_table: str
    criterion_id: str | None = None
    season: str = "road"


def municipal_overview(
    region_id: str,
    municipalities: MunicipalityQueries,
    repository: MunicipalIndexRepository,
    criterion_id: str | None = None,
    published: Callable[[Municipality], list[MunicipalNormativeValue]] | None = None,
    season: str = "road",
    published_overview: Callable[[list[Municipality], str], dict[str, list[MunicipalNormativeValue]]] | None = None,
) -> MunicipalOverview:
    if season not in {"road", "summer", "winter"} or (criterion_id is not None and criterion_id not in {f"N{i:02}" for i in range(1, 10)}):
        raise InvalidQuery("Invalid municipal overview metric or season")
    boundaries = municipalities.run(region_id)
    source = repository.points(region_id, season)
    regional = aggregate_metric(source.points, "hansen_idx", "index_points")
    batch = published_overview(boundaries.items, criterion_id) if published_overview and criterion_id else None
    items = []
    for municipality in boundaries.items:
        points = municipal_points(source.points, municipality.coordinates)
        metric = aggregate_metric(points, "hansen_idx", "index_points")
        difference = (
            metric.value - regional.value
            if metric.value is not None and regional.value is not None
            else None
        )
        reasons = []
        if metric.value is None:
            reasons.append("connectivity_unavailable")
        elif difference is not None and difference < 0:
            reasons.append("below_region_connectivity")
        if metric.population_coverage is not None and metric.population_coverage < 1:
            reasons.append("incomplete_population_coverage")
        rows = (batch.get(municipality.id, []) if batch is not None else published(municipality) if published and criterion_id else [])
        service = service_priority(criterion_id, rows) if criterion_id else None
        if service and service.confirmed_deficit_points:
            reasons.append("confirmed_service_deficit")
        if service and service.unresolved_points:
            reasons.append("incomplete_service_measurements")
        items.append(MunicipalOverviewItem(municipality.id, municipality.name, metric, difference, reasons, service))
    items.sort(key=lambda item: (
        item.connectivity.value is None,
        item.connectivity.value if item.connectivity.value is not None else 0,
        item.name,
    ))
    if criterion_id:
        items.sort(key=lambda item: (
            item.service is None or item.service.status != "available",
            -(item.service.confirmed_deficit_percent or 0) if item.service else 0,
            item.name,
        ))
    return MunicipalOverview(region_id, items, regional, source.model_version, source.artifact_version, source.source_table, criterion_id, season)
