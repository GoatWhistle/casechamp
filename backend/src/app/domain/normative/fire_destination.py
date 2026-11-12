import re
from dataclasses import dataclass
from datetime import datetime
from math import isfinite
from typing import Literal

OriginBasis = Literal["settlements", "fire_objects", "residential_references"]
FireOriginBasis = Literal["settlements", "fire_objects"]


@dataclass(frozen=True, slots=True, kw_only=True)
class FireDestination:
    id: str
    name: str
    address: str
    region: str
    latitude: float
    longitude: float
    source_url: str
    observed_at: str
    reference_status: Literal["candidate_point", "verified_object"] = "candidate_point"
    source_sha256: str | None = None

    def __post_init__(self) -> None:
        for value in (self.id, self.name, self.address, self.region):
            if not isinstance(value, str) or not value.strip():
                raise ValueError(
                    "Fire destinations require identifiers, names, addresses and region"
                )
        if not isinstance(self.source_url, str) or not self.source_url.startswith(
            ("http://", "https://")
        ):
            raise ValueError("Fire destinations require their source URL")
        if not isinstance(self.observed_at, str):
            raise TypeError("Fire destination observations require ISO dates")
        observed = datetime.fromisoformat(self.observed_at)
        if len(self.observed_at) > 10 and observed.tzinfo is None:
            raise ValueError("Fire destination timestamps require a timezone")
        if self.reference_status not in {"candidate_point", "verified_object"}:
            raise ValueError("Unknown fire destination reference status")
        for coordinate, limit in [(self.latitude, 90), (self.longitude, 180)]:
            if (
                isinstance(coordinate, bool)
                or not isinstance(coordinate, (int, float))
                or not isfinite(coordinate)
                or abs(coordinate) > limit
            ):
                raise ValueError("Invalid fire destination coordinates")
        if self.source_sha256 is not None and (
            not isinstance(self.source_sha256, str)
            or re.fullmatch(r"[0-9a-f]{64}", self.source_sha256) is None
        ):
            raise ValueError(
                "Fire destination source hash requires 64 lowercase hexadecimal digits"
            )
