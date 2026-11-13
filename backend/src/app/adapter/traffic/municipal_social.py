from collections.abc import Callable
from typing import Any

from synthetic_traffic.incremental import IncrementalBaseline
from synthetic_traffic.model import Network

from app.adapter.traffic.social_routing import SocialRouting
from app.domain.errors import DataUnavailable
from app.domain.normative.scenario_index import scenario_policy
from app.usecase.municipal_scenarios import MunicipalScenarioRequest
from app.usecase.municipal_social import (
    SOCIAL_CRITERIA,
    MunicipalSocialEffect,
    MunicipalSocialPoint,
    MunicipalSocialSource,
    MunicipalSocialSources,
    summarize_social,
)


class MunicipalSocialAccess:
    def __init__(self, sources: MunicipalSocialSources) -> None:
        self.sources = sources

    def evaluate(
        self, request: MunicipalScenarioRequest, baseline: IncrementalBaseline,
        changed: Network, hours: Any, check: Callable[[], None],
    ) -> tuple[MunicipalSocialEffect, ...]:
        metadata = baseline.metadata.get("source", {})
        if "bounds" not in metadata or metadata["bounds"] is not None:
            return tuple(unavailable(criterion, "social_network_clipped_or_unknown") for criterion in SOCIAL_CRITERIA)
        revision = next((item["value"] for item in metadata.get("metadata", [])
                         if item["key"] == "graph_revision"), None)
        if not revision:
            return tuple(unavailable(criterion, "social_graph_revision_missing") for criterion in SOCIAL_CRITERIA)
        check()
        router = SocialRouting(baseline.network)
        before_graph = router.matrix(baseline.network, baseline.assignment.hours)
        after_graph = router.matrix(changed, hours)
        result = []
        cached_key: object = None
        cached_routes: Any = None
        for criterion in SOCIAL_CRITERIA:
            check()
            try:
                source = self.sources.load(request.region_id, request.municipality_id, criterion)
            except DataUnavailable:
                result.append(unavailable(criterion, "social_source_unavailable"))
                continue
            if source.graph_revision != revision:
                result.append(unavailable(criterion, "social_graph_mismatch"))
                continue
            key = (tuple(source.facilities), tuple((r.id, r.routing_node, r.approach_metres) for r in source.rows))
            if key != cached_key:
                targets = router.targets(source.facilities)
                before = router.evaluate(before_graph, source.rows, targets)
                check()
                after = router.evaluate(after_graph, source.rows, targets)
                cached_routes = (targets, before, after)
                cached_key = key
            targets, before, after = cached_routes
            if not targets:
                result.append(unavailable(criterion, "social_facilities_unattached"))
                continue
            result.append(compare_source(source, before, after, len(targets)))
        check()
        return tuple(result)


def unavailable(criterion: str, reason: str) -> MunicipalSocialEffect:
    return MunicipalSocialEffect(criterion, scenario_policy(criterion).thresholds[0], reason=reason)


def compare_source(
    source: MunicipalSocialSource,
    before: list[tuple[float | None, str | None, bool]],
    after: list[tuple[float | None, str | None, bool]],
    attached: int,
) -> MunicipalSocialEffect:
    facilities = {item.id: item.name for item in source.facilities}
    threshold = scenario_policy(source.criterion_id).thresholds[0]
    points = []
    for row, (old, old_id, _), (new, new_id, resolved) in zip(source.rows, before, after, strict=True):
        points.append(MunicipalSocialPoint(
            row.id, row.name, row.latitude, row.longitude, old, new,
            new - old if old is not None and new is not None else None,
            old_id, new_id, facilities.get(new_id) if new_id else None,
            (new is not None) if resolved else None,
            old is not None and old <= threshold and resolved and (new is None or new > threshold),
        ))
    return summarize_social(source, points, attached)
