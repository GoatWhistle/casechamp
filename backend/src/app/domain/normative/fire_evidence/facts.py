from dataclasses import dataclass
from datetime import date
from math import isfinite
from typing import ClassVar, Literal

from app.domain.normative.transport_facts import TransportFacts


@dataclass(frozen=True, slots=True, kw_only=True)
class FireFacts(TransportFacts):
    allowed_transport_modes: ClassVar[frozenset[str]] = frozenset({"emergency_response"})
    settlement_type_verified: bool = False
    settlement_type: Literal["urban", "rural"] | None = None
    speed_verified: bool = False
    speed_kmh: float | None = None
    speed_source_url: str | None = None
    profile_assumption: str | None = None
    adverse_conditions_verified: bool = False
    vehicle_access_verified: bool = False
    directionality_verified: bool = False
    operational_readiness_verified: bool = False
    destination_objects_verified: bool = False
    population_scope: Literal["measured_objects"] | None = None
    population_partition_verified: bool = False
    measurement_definition_verified: bool = False
    measurement_definition: Literal["depot_to_object_travel"] | None = None
    method_source_url: str | None = None
    method_currentness_verified: bool = False
    method_edition_date: str | None = None

    def __post_init__(self) -> None:
        TransportFacts.__post_init__(self)
        if self.settlement_type not in {None, "urban", "rural"}:
            raise ValueError("Unknown fire destination settlement type")
        if self.settlement_type_verified and self.settlement_type is None:
            raise ValueError("Verified fire settlement type requires a category")
        if self.speed_kmh is not None and (
            not isfinite(self.speed_kmh) or not 0 < self.speed_kmh <= 200
        ):
            raise ValueError("Verified fire speed must be finite and between zero and 200 km/h")
        if (
            self.profile_assumption is not None
            and not 8 <= len(self.profile_assumption.strip()) <= 500
        ):
            raise ValueError("Fire evidence requires a profile description in 8 to 500 characters")
        if self.speed_verified and (
            self.speed_kmh is None or not self.speed_source_url or not self.profile_assumption
        ):
            raise ValueError("Verified fire speed requires its value and source")
        if self.population_scope not in {None, "measured_objects"}:
            raise ValueError("Fire population must refer to measured objects")
        if self.population_verified and (
            self.population_scope != "measured_objects" or not self.population_partition_verified
        ):
            raise ValueError(
                "Verified fire population requires measured-object scope and a disjoint partition"
            )
        if self.measurement_definition not in {None, "depot_to_object_travel"}:
            raise ValueError("The fire model supports depot-to-object travel only")
        if self.measurement_definition_verified and (
            not self.method_source_url or self.measurement_definition is None
        ):
            raise ValueError("Verified fire measurement requires its definition and source")
        if self.method_edition_date is not None:
            date.fromisoformat(self.method_edition_date)
        if self.method_currentness_verified and (
            not self.method_edition_date or not self.method_source_url
        ):
            raise ValueError("Verified fire methodology requires its edition and source")
        for source in (self.speed_source_url, self.method_source_url):
            if source is not None and not source.startswith(("https://", "http://")):
                raise ValueError("Fire evidence sources require HTTP URLs")
