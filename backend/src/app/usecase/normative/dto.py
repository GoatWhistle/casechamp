from dataclasses import dataclass
from datetime import datetime

from app.domain.normative.comparison import RouteComparison
from app.domain.normative.fire import FireProfile
from app.domain.normative.fire_destination import FireDestination, OriginBasis
from app.domain.normative.fire_evidence.facts import FireFacts
from app.domain.normative.library.facts import LibraryFacts
from app.domain.normative.medical.facts import MedicalFacts
from app.domain.normative.model import AccessRow, Coverage, Criterion, Facility
from app.domain.normative.rules import RuleSet
from app.domain.normative.walking_facts import WalkingFacts
from app.usecase.normative.route import MODEL_REVISION


@dataclass(frozen=True, slots=True)
class Assessment:
    criterion: Criterion
    facilities: list[Facility]
    graph_revision: str
    region: str
    baseline: Coverage
    scenario: Coverage
    baseline_rows: list[AccessRow]
    rows: list[AccessRow]
    closed_way_ids: list[int]
    coverage_loss_pp: float | None
    run_id: str | None = None
    model_revision: str = MODEL_REVISION
    comparison: RouteComparison | None = None
    ignored_way_ids: tuple[int, ...] = ()
    fire_profile: FireProfile | None = None
    saved_at: datetime | None = None
    rule_sets: tuple[RuleSet, ...] = ()
    walking_facts: tuple[WalkingFacts, ...] = ()
    library_facts: tuple[LibraryFacts, ...] = ()
    medical_facts: tuple[MedicalFacts, ...] = ()
    fire_facts: tuple[FireFacts, ...] = ()
    fire_destinations: tuple[FireDestination, ...] = ()
    qualification_as_of: datetime | None = None
    origin_basis: OriginBasis = "settlements"


@dataclass(frozen=True, slots=True)
class SavedRun:
    criterion: Criterion
    facilities: list[Facility]
    graph_revision: str
    region: str
    baseline_rows: list[AccessRow]
    rows: list[AccessRow]
    closed_way_ids: list[int]
    run_id: str
    model_revision: str = "unversioned"
    ignored_way_ids: tuple[int, ...] = ()
    fire_profile: FireProfile | None = None
    saved_at: datetime | None = None
    rule_sets: tuple[RuleSet, ...] = ()
    qualification_as_of: datetime | None = None
    origin_basis: OriginBasis = "settlements"


@dataclass(frozen=True, slots=True)
class AssessmentReceipt:
    run_id: str
    saved_at: datetime
