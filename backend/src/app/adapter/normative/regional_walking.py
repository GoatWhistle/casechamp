from collections.abc import Callable
from threading import Lock

from app.adapter.normative.walking_routing import WalkingNormativeRouting
from app.usecase.normative.interface import NormativeRouting
from app.usecase.normative.walking import PedestrianRepository


class RegionalWalkingFactory:
    def __init__(self, repository: Callable[[str], PedestrianRepository]) -> None:
        self.repository = repository
        self.lock = Lock()
        self.current: tuple[str, WalkingNormativeRouting] | None = None

    def for_region(self, region_id: str) -> NormativeRouting:
        with self.lock:
            if self.current is None or self.current[0] != region_id:
                self.current = (
                    region_id,
                    WalkingNormativeRouting(self.repository(region_id), spherical=True),
                )
            return self.current[1]
