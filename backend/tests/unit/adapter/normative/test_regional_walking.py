from app.adapter.normative.regional_walking import RegionalWalkingFactory
from app.usecase.normative.walking import PedestrianNetwork


class NetworkRepository:
    current_revision = "first"

    def network(self, revision: str | None = None) -> PedestrianNetwork:
        return PedestrianNetwork(
            revision or self.current_revision,
            [(0, 55.0, 37.0), (1, 55.001, 37.0)],
            [(0, 1, 100.0, 1), (1, 0, 100.0, 1)],
            "https://example.test/snapshot",
            "2026-11-13",
        )


def test_new_snapshot_replaces_cached_graph_without_changing_existing_routing() -> None:
    repository = NetworkRepository()
    factory = RegionalWalkingFactory(
        lambda region: repository, lambda region: repository.current_revision
    )
    original = factory.for_region("region")
    assert original.revision == "first"
    assert factory.for_region("region") is original
    repository.current_revision = "second"
    updated = factory.for_region("region")
    assert updated is not original
    assert updated.revision == "second"
    assert original.revision == "first"
