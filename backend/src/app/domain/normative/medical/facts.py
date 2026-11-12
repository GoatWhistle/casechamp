from dataclasses import dataclass
from math import isfinite
from typing import Literal

from app.domain.normative.scope import ADULT_CARDIOLOGY
from app.domain.normative.transport_facts import TransportFacts


@dataclass(frozen=True, slots=True, kw_only=True)
class MedicalFacts(TransportFacts):
    service: str
    population_group: Literal["adults"] | None = None
    ownership_scope_verified: bool = False
    ownership_applicable: bool | None = None
    facility_form_verified: bool = False
    adult_profile_verified: bool = False
    catchment_verified: bool = False
    catchment_source_url: str | None = None
    regional_adjustment_verified: bool = False
    regional_adjustment_source_url: str | None = None
    threshold_minutes: float | None = None

    def __post_init__(self) -> None:
        TransportFacts.__post_init__(self)
        if self.service not in ADULT_CARDIOLOGY:
            raise ValueError("Medical evidence requires a supported care form")
        if self.population_group not in {None, "adults"}:
            raise ValueError("Adult cardiology requires the adult population group")
        if self.population_verified and self.population_group != "adults":
            raise ValueError("Verified medical population must describe adults")
        if self.catchment_verified and not self.catchment_source_url:
            raise ValueError("Verified catchments require their source")
        if self.threshold_minutes is not None and (
            not isfinite(self.threshold_minutes) or self.threshold_minutes <= 0
        ):
            raise ValueError("Medical transport thresholds must be finite and positive")
        if self.regional_adjustment_verified and (
            not self.regional_adjustment_source_url or self.threshold_minutes is None
        ):
            raise ValueError(
                "Verified regional adjustment requires a source and selected threshold"
            )
        for source in (self.catchment_source_url, self.regional_adjustment_source_url):
            if source is not None and not source.startswith(("https://", "http://")):
                raise ValueError("Medical evidence sources require HTTP URLs")
