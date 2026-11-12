from types import SimpleNamespace
from typing import cast

from app.domain.municipal_metrics import MunicipalObservation
from app.usecase.municipal_indices import MunicipalIndexQueries, MunicipalIndexSource
from app.usecase.municipalities import Municipality, MunicipalityQueries


class Source:
    def __init__(self) -> None:
        self.calls = 0

    def points(self, region_id: str, season: str) -> MunicipalIndexSource:
        self.calls += 1
        return MunicipalIndexSource(
            [
                MunicipalObservation("inside", 40.1, 44.1, 100, {"hansen_idx": 10}, True),
                MunicipalObservation("other", 42, 46, 300, {"hansen_idx": 30}, True),
            ],
            "model",
            "artifact",
            "actual-table",
        )


def test_municipal_index_is_spatial_subset_with_separate_same_source_region_reference() -> None:
    municipality = Municipality(
        "real-id",
        "07000000",
        "Real",
        6,
        [[[(40, 44), (41, 44), (41, 45), (40, 45), (40, 44)]]],
        "https://source",
        "2026-11-11",
        "abc",
        "polygon",
        1,
    )
    municipalities = cast(
        MunicipalityQueries,
        SimpleNamespace(run=lambda region: SimpleNamespace(items=[municipality])),
    )
    source = Source()
    queries = MunicipalIndexQueries(municipalities, source)
    response = queries.run("07000000", "real-id")
    assert response.connectivity.value == 10
    assert response.connectivity.population == 100
    assert response.region_connectivity.value == 25
    assert response.artifact_version == "artifact"
    assert queries.run("07000000", "real-id") is response
    assert source.calls == 1
