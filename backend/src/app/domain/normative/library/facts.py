import re
from dataclasses import dataclass

from app.domain.normative.territory import MunicipalityType
from app.domain.normative.transport_facts import TransportFacts


@dataclass(frozen=True, slots=True, kw_only=True)
class LibraryFacts(TransportFacts):
    municipality_type: MunicipalityType | None = None
    municipality_code: str | None = None

    def __post_init__(self) -> None:
        TransportFacts.__post_init__(self)
        if self.municipality_type not in {None, "urban_okrug", "municipal_okrug"}:
            raise ValueError("Unknown library municipality category")
        if (
            self.municipality_code is not None
            and re.fullmatch(r"[0-9]{8}", self.municipality_code) is None
        ):
            raise ValueError("Municipality evidence requires an eight-digit code")
        if self.jurisdiction_verified and (
            not self.municipality_type or not self.municipality_code
        ):
            raise ValueError("Verified jurisdiction requires a municipality")
