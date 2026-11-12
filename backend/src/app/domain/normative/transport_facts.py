from dataclasses import dataclass, fields
from datetime import UTC, date, datetime
from math import isfinite
from types import UnionType
from typing import ClassVar, get_args, get_origin


@dataclass(frozen=True, slots=True, kw_only=True)
class TransportFacts:
    allowed_transport_modes: ClassVar[frozenset[str]] = frozenset({"car"})

    origin_id: str
    source_url: str
    observed_at: str
    valid_from: str
    valid_until: str
    facts_verified: bool = False
    legal_currentness_verified: bool = False
    normative_source_url: str | None = None
    legal_edition_date: str | None = None
    jurisdiction_verified: bool = False
    territory: str | None = None
    planning_scope: bool | None = None
    population_verified: bool = False
    population: int | None = None
    population_reference: str | None = None
    origin_reference_verified: bool = False
    origin_latitude: float | None = None
    origin_longitude: float | None = None
    routing_node: int | None = None
    approach_metres: float | None = None
    measurement_verified: bool = False
    measurement_graph_revision: str | None = None
    transport_method_verified: bool = False
    transport_mode: str | None = None
    eligible_facility_ids: tuple[str, ...] = ()
    eligible_inventory_complete: bool = False
    service_eligible: bool | None = None
    service_active: bool | None = None
    scenario_verified: bool = False
    verified_closed_way_ids: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        if not self.origin_id or not self.source_url.startswith(("http://", "https://")):
            raise ValueError("Transport evidence requires an origin and source URL")
        observed = datetime.fromisoformat(self.observed_at)
        if len(self.observed_at) > 10 and observed.tzinfo is None:
            raise ValueError("Evidence timestamps require a timezone")
        if date.fromisoformat(self.valid_from) > date.fromisoformat(self.valid_until):
            raise ValueError("Transport evidence has an inverted validity interval")
        if self.legal_edition_date is not None:
            date.fromisoformat(self.legal_edition_date)
        if (
            self.transport_mode is not None
            and self.transport_mode not in self.allowed_transport_modes
        ):
            raise ValueError("Evidence transport mode does not match the routing model")
        for value, limit in [(self.origin_latitude, 90), (self.origin_longitude, 180)]:
            if value is not None and (not isfinite(value) or abs(value) > limit):
                raise ValueError("Invalid transport origin coordinates")
        if self.routing_node is not None and (
            type(self.routing_node) is not int or self.routing_node < 0
        ):
            raise ValueError("Invalid transport routing node")
        if self.approach_metres is not None and (
            not isfinite(self.approach_metres) or not 0 <= self.approach_metres <= 5000
        ):
            raise ValueError("Invalid transport approach length")
        if self.population is not None and (
            type(self.population) is not int or self.population < 0
        ):
            raise ValueError("Population must be a nonnegative integer")
        if self.population_verified and (self.population is None or not self.population_reference):
            raise ValueError("Verified population requires its cohort reference")
        if self.legal_currentness_verified and (
            not self.legal_edition_date or not self.normative_source_url
        ):
            raise ValueError("Verified law requires the selected edition and source")
        if self.jurisdiction_verified and (not self.territory):
            raise ValueError("Verified jurisdiction requires a territory")
        if self.measurement_verified and (
            not self.measurement_graph_revision
            or self.routing_node is None
            or self.approach_metres is None
            or self.origin_latitude is None
            or self.origin_longitude is None
        ):
            raise ValueError("Verified measurements require frozen graph attachments")
        if (
            not isinstance(self.eligible_facility_ids, tuple)
            or any(not isinstance(key, str) or not key for key in self.eligible_facility_ids)
            or len(set(self.eligible_facility_ids)) != len(self.eligible_facility_ids)
        ):
            raise ValueError("Eligible facility identifiers must be a unique tuple")
        if (
            not isinstance(self.verified_closed_way_ids, tuple)
            or any(type(key) is not int or key <= 0 for key in self.verified_closed_way_ids)
            or len(set(self.verified_closed_way_ids)) != len(self.verified_closed_way_ids)
            or len(self.verified_closed_way_ids) > 20
        ):
            raise ValueError("Verified closures must be a unique positive tuple of at most twenty")
        for field in fields(self):
            value = getattr(self, field.name)
            kinds = get_args(field.type) if get_origin(field.type) is UnionType else (field.type,)
            required = value is not None or type(None) not in kinds
            if required and bool in kinds and type(value) is not bool:
                raise ValueError(f"Expected boolean evidence: {field.name}")
            if required and str in kinds and type(value) is not str:
                raise ValueError(f"Expected string evidence: {field.name}")
            if (
                value is not None
                and float in kinds
                and (isinstance(value, bool) or not isinstance(value, (int, float)))
            ):
                raise ValueError(f"Expected numeric evidence: {field.name}")

    def active_on(self, instant: datetime) -> bool:
        if instant.tzinfo is None:
            raise ValueError("The assessment clock must be timezone-aware")
        instant = instant.astimezone(UTC)
        observed = datetime.fromisoformat(self.observed_at)
        seen = (
            observed.date() <= instant.date()
            if len(self.observed_at) == 10
            else observed <= instant
        )
        return seen and date.fromisoformat(self.valid_from) <= instant.date() <= date.fromisoformat(
            self.valid_until
        )
