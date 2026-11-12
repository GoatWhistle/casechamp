from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime

from app.domain.errors import DataUnavailable
from app.domain.normative.fire import FireProfile, SettlementContext
from app.domain.normative.fire_evidence.facts import FireFacts
from app.domain.normative.fire_evidence.qualification import apply_fire_evidence
from app.domain.normative.library.facts import LibraryFacts
from app.domain.normative.library.qualification import apply_library_evidence
from app.domain.normative.medical.facts import MedicalFacts
from app.domain.normative.medical.qualification import apply_medical_evidence
from app.domain.normative.model import AccessRow, Criterion, Facility, Origin
from app.domain.normative.scope import ADULT_CARDIOLOGY
from app.domain.normative.territory import TerritoryContext, apply_library_conditions
from app.usecase.normative.fire_evaluation import evaluate_fire_targets
from app.usecase.normative.interface import NormativeRepository, NormativeRouting
from app.usecase.normative.library_evaluation import evaluate_library_targets
from app.usecase.normative.medical_evaluation import evaluate_medical_targets


@dataclass(frozen=True, slots=True, kw_only=True)
class TransportConditions:
    criterion: Criterion
    library_facts: list[LibraryFacts]
    medical_facts: list[MedicalFacts]
    fire_facts: list[FireFacts]
    territories: list[TerritoryContext]
    settlements: list[SettlementContext]
    instant: datetime | None
    fire_profile: FireProfile | None

    def evaluate(
        self,
        routing: NormativeRouting,
        origins: list[Origin],
        facilities: list[Facility],
        closed: list[int],
    ) -> list[AccessRow]:
        if self.instant is not None:
            if self.library_facts:
                return evaluate_library_targets(
                    routing,
                    origins,
                    facilities,
                    self.criterion.threshold,
                    closed,
                    self.library_facts,
                    self.instant,
                )
            if self.medical_facts:
                return evaluate_medical_targets(
                    routing,
                    origins,
                    facilities,
                    self.criterion.threshold,
                    closed,
                    self.medical_facts,
                    self.instant,
                )
            if self.fire_facts:
                return evaluate_fire_targets(
                    routing,
                    origins,
                    facilities,
                    self.criterion.threshold,
                    closed,
                    self.fire_facts,
                    self.instant,
                )
        return routing.evaluate(origins, facilities, self.criterion.threshold, closed)

    def qualify(
        self, rows: list[AccessRow], facilities: list[Facility], revision: str, closed: list[int]
    ) -> list[AccessRow]:
        try:
            if self.criterion.service in ADULT_CARDIOLOGY:
                return apply_medical_evidence(
                    self.criterion,
                    rows,
                    self.medical_facts,
                    facilities,
                    revision,
                    self.instant,
                    closed,
                )
            if self.criterion.service == "fire":
                return apply_fire_evidence(
                    self.criterion,
                    rows,
                    self.settlements,
                    self.fire_facts,
                    facilities,
                    revision,
                    self.instant,
                    closed,
                    self.fire_profile,
                )
            if self.criterion.service == "library":
                if self.library_facts and self.instant is not None:
                    return apply_library_evidence(
                        self.criterion,
                        rows,
                        self.territories,
                        self.library_facts,
                        facilities,
                        revision,
                        self.instant,
                        closed,
                    )
                return apply_library_conditions(rows, self.territories)
        except ValueError as error:
            raise DataUnavailable("Transport qualification evidence is inconsistent") from error
        return rows


def load_transport_conditions(
    repository: NormativeRepository,
    criterion: Criterion,
    origins: list[Origin],
    clock: Callable[[], datetime] | None,
    fire_profile: FireProfile | None,
) -> TransportConditions:
    libraries = repository.library_facts() if criterion.service == "library" else []
    medical = (
        repository.medical_facts(criterion.service) if criterion.service in ADULT_CARDIOLOGY else []
    )
    fire = repository.fire_facts() if criterion.service == "fire" else []
    facts = [*libraries, *medical, *fire]
    instant = None
    if facts:
        if clock is None:
            raise DataUnavailable("Transport evidence requires an assessment clock")
        instant = clock()
        if instant.tzinfo is None:
            raise DataUnavailable("The assessment clock must include a timezone")
        instant = instant.astimezone(UTC).replace(microsecond=instant.microsecond // 1000 * 1000)
        if len({f.origin_id for f in facts}) != len(facts) or {f.origin_id for f in facts} - {
            o.id for o in origins
        }:
            raise DataUnavailable("Transport evidence has duplicate or unknown origins")
    return TransportConditions(
        criterion=criterion,
        library_facts=libraries,
        medical_facts=medical,
        fire_facts=fire,
        territories=repository.territories() if criterion.service == "library" else [],
        settlements=repository.settlement_types() if criterion.service == "fire" else [],
        instant=instant,
        fire_profile=fire_profile,
    )
