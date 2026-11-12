from collections.abc import Callable
from threading import Lock

from app.adapter.normative.walking_routing import WalkingNormativeRouting
from app.usecase.normative.interface import NormativeRouting
from app.usecase.normative.walking import PedestrianRepository


class RegionalWalkingFactory:
    def __init__(
        self,
        repository: Callable[[str], PedestrianRepository],
        revision: Callable[[str], str] | None = None,
    ) -> None:
        self.repository = repository
        self.revision = revision
        self.lock = Lock()
        self.current: tuple[str, WalkingNormativeRouting] | None = None
        self.current_revision: str | None = None

    def for_region(self, region_id: str) -> NormativeRouting:
        with self.lock:
            revision = self.revision(region_id) if self.revision else None
            if (
                self.current is None
                or self.current[0] != region_id
                or self.current_revision != revision
            ):
                self.current = (
                    region_id,
                    WalkingNormativeRouting(self.repository(region_id), spherical=True),
                )
                self.current_revision = revision
            return self.current[1]
