from collections.abc import Callable
from threading import Lock

from app.adapter.normative.walking_graph import WalkingGraph
from app.adapter.transit.walking import TransitWalking
from app.usecase.normative.walking import PedestrianRepository


class TransitWalkingFactory:
    def __init__(self, repository: Callable[[str], PedestrianRepository], revision: Callable[[str], str]) -> None:
        self.repository = repository
        self.revision = revision
        self.lock = Lock()
        self.current: tuple[str, TransitWalking] | None = None

    def for_region(self, region: str) -> TransitWalking:
        with self.lock:
            revision = self.revision(region)
            if self.current is None or self.current[0] != region or self.current[1].revision != revision:
                self.current = (region, TransitWalking(WalkingGraph(self.repository(region).network(revision), spherical=True)))
            return self.current[1]
