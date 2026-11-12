from collections.abc import Callable
from dataclasses import replace
from datetime import datetime

from app.domain.errors import DataUnavailable, InvalidQuery
from app.domain.normative.comparison import compare_routes
from app.domain.normative.fire import FireProfile
from app.domain.normative.fire_destination import FireDestination, FireOriginBasis, OriginBasis
from app.domain.normative.model import AccessRow, Criterion, Facility, coverage
from app.domain.normative.rules import RuleSet
from app.domain.normative.walking_assessment import apply_walking_conditions, walking_entrances
from app.usecase.normative.dto import Assessment
from app.usecase.normative.fire_destinations import describe_objects, object_origins
from app.usecase.normative.interface import (
    NormativeFireRouting,
    NormativeOriginAttachment,
    NormativeRepository,
    NormativeRouting,
)
from app.usecase.normative.route import NormativeRoute, RouteStage
from app.usecase.normative.routes import NormativeRoutes
from app.usecase.normative.routing import routing_for
from app.usecase.normative.transport_conditions import load_transport_conditions
from app.usecase.normative.walking_evaluation import evaluate_walking_targets


class NormativeQueries:
    def __init__(
        self,
        repository: NormativeRepository,
        routing: NormativeRouting | None,
        walking: NormativeRouting | None = None,
        fire: NormativeFireRouting | None = None,
        clock: Callable[[], datetime] | None = None,
        object_attachment: NormativeOriginAttachment | None = None,
    ) -> None:
        self.repository = repository
        self.routing = routing
        self.walking = walking
        self.fire = fire
        self.clock = clock
        self.object_attachment = object_attachment

    def catalog(self) -> list[Criterion]:
        return self.repository.criteria()

    def latest(self, criterion_id: str) -> Assessment | None:
        self.criterion(criterion_id)
        saved = self.repository.latest(criterion_id)
        if saved is None:
            return None
        before, after = coverage(saved.baseline_rows), coverage(saved.rows)
        loss = (
            before.lower_percent - after.lower_percent
            if before.lower_percent is not None and after.lower_percent is not None
            else None
        )
        return Assessment(
            saved.criterion,
            saved.facilities,
            saved.graph_revision,
            saved.region,
            before,
            after,
            saved.baseline_rows,
            saved.rows,
            saved.closed_way_ids,
            loss,
            saved.run_id,
            model_revision=saved.model_revision,
            comparison=compare_routes(saved.baseline_rows, saved.rows, saved.criterion.unit),
            ignored_way_ids=saved.ignored_way_ids,
            fire_profile=saved.fire_profile,
            saved_at=saved.saved_at,
            rule_sets=saved.rule_sets,
            qualification_as_of=saved.qualification_as_of,
            origin_basis=saved.origin_basis,
        )

    def facilities(self, criterion_id: str) -> list[Facility]:
        return self.repository.facilities(self.criterion(criterion_id).service)

    def fire_destinations(self) -> list[FireDestination]:
        return self.repository.fire_destinations(self.criterion("N03").territory)

    def criterion(self, criterion_id: str) -> Criterion:
        result = next((c for c in self.catalog() if c.id == criterion_id), None)
        if result is None:
            raise InvalidQuery("Unknown normative criterion")
        return result

    def assess(
        self,
        criterion_id: str,
        closed_way_ids: list[int],
        fire_profile: FireProfile | None = None,
        origin_basis: FireOriginBasis = "settlements",
    ) -> Assessment:
        if origin_basis not in {"settlements", "fire_objects"}:
            raise InvalidQuery("Unknown fire origin basis")
        criterion = self.criterion(criterion_id)
        routing = routing_for(criterion, self.routing, self.walking, self.fire, fire_profile)
        facilities = self.repository.facilities(criterion.service)
        if not facilities:
            raise DataUnavailable("No sourced facilities have been imported for this service")
        destinations: list[FireDestination] = []
        basis: OriginBasis = "residential_references" if criterion.mode == "walk" else "settlements"
        if origin_basis == "fire_objects":
            if criterion.service != "fire":
                raise InvalidQuery("Object destinations only apply to N03")
            destinations = self.repository.fire_destinations(criterion.territory)
            if any(d.region != criterion.territory for d in destinations):
                raise DataUnavailable("Fire destination objects belong to another region")
            origins = object_origins(destinations, self.object_attachment, routing.revision)
            basis = "fire_objects"
        else:
            origins = (
                self.repository.walking_origins(routing.revision)
                if criterion.mode == "walk"
                else self.repository.origins(criterion.territory)
            )
        facts = self.repository.walking_facts(criterion.service) if criterion.mode == "walk" else []
        if facts:
            origins = walking_entrances(origins, facts)
        if not origins:
            raise DataUnavailable("No population origins for the selected territory")
        conditions = load_transport_conditions(
            self.repository, criterion, origins, self.clock, fire_profile
        )

        def evaluate(closed: list[int]) -> list[AccessRow]:
            if criterion.mode == "walk":
                return evaluate_walking_targets(
                    routing, origins, facilities, criterion.threshold, closed, facts
                )
            return describe_objects(
                conditions.evaluate(routing, origins, facilities, closed), destinations
            )

        base = conditions.qualify(evaluate([]), facilities, routing.revision, [])
        rows = (
            conditions.qualify(
                evaluate(closed_way_ids), facilities, routing.revision, closed_way_ids
            )
            if closed_way_ids
            else base
        )
        rule_sets: tuple[RuleSet, ...] = ()
        if criterion.mode == "walk":
            base, rows, rule_sets = apply_walking_conditions(
                criterion.service, base, rows, facts, closed_way_ids, routing.revision
            )
        before, after = coverage(base), coverage(rows)
        loss = (
            before.lower_percent - after.lower_percent
            if before.lower_percent is not None and after.lower_percent is not None
            else None
        )
        result = Assessment(
            criterion,
            facilities,
            routing.revision,
            criterion.territory,
            before,
            after,
            base,
            rows,
            closed_way_ids,
            loss,
            comparison=compare_routes(base, rows, criterion.unit),
            fire_profile=fire_profile,
            rule_sets=rule_sets,
            walking_facts=tuple(facts),
            library_facts=tuple(conditions.library_facts),
            medical_facts=tuple(conditions.medical_facts),
            fire_facts=tuple(conditions.fire_facts),
            qualification_as_of=conditions.instant,
            origin_basis=basis,
            fire_destinations=tuple(destinations),
            ignored_way_ids=tuple(routing.missing_ways(closed_way_ids)),
        )
        receipt = self.repository.save(result)
        return replace(result, run_id=receipt.run_id, saved_at=receipt.saved_at)

    def route(self, run_id: str, origin_id: str, stage: RouteStage) -> NormativeRoute:
        return NormativeRoutes(self.repository, self.routing, self.walking, self.fire).get(
            run_id, origin_id, stage
        )
