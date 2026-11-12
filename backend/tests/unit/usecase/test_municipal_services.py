from types import SimpleNamespace
from typing import cast

from app.domain.municipal_metrics import MunicipalObservation
from app.domain.normative.model import AccessRow, Facility, Origin
from app.usecase.municipal_services import MunicipalServiceQueries
from app.usecase.municipalities import Municipality
from app.usecase.normative.interface import NormativeRouting
from app.usecase.normative.regional_catalog import RegionalCatalogQueries
from app.usecase.normative.regional_models import RegionalWalkingModels


class Routing:
    revision = "real-snapshot"

    def __init__(self, walking: bool = False) -> None:
        self.walking = walking
        self.calls = 0

    def evaluate(
        self,
        origins: list[Origin],
        facilities: list[Facility],
        threshold: float,
        closed_way_ids: list[int],
    ) -> list[AccessRow]:
        self.calls += 1
        return [
            AccessRow(
                o.id,
                o.name,
                None,
                o.latitude,
                o.longitude,
                "f",
                30 + i * 60,
                None,
                "unknown",
                distance_metres=200 + i * 700 if self.walking else None,
            )
            for i, o in enumerate(origins)
        ]

    def missing_ways(self, ids: list[int]) -> list[int]:
        return []

    def trace(self, *args: object) -> object:
        raise AssertionError("No trace is required")


def test_async_services_reuse_imported_thresholds_and_true_residential_origins() -> None:
    facility = Facility(
        "f",
        "school",
        "Sourced",
        "",
        "https://example.org",
        "2026-11-11",
        44,
        40,
        "osm",
        "osm_institution_pin",
    )
    catalog = cast(
        RegionalCatalogQueries,
        SimpleNamespace(catalog=lambda *args: SimpleNamespace(facilities=[facility])),
    )
    road, walking = Routing(), Routing(True)
    service = MunicipalServiceQueries(
        catalog,
        cast(NormativeRouting, road),
        cast(RegionalWalkingModels, SimpleNamespace(for_region=lambda region: walking)),
        lambda revision: [
            Origin("home1", "Home1", None, None, None, 44.2, 40.2),
            Origin("home2", "Home2", None, None, None, 44.5, 40.5),
            Origin("outside", "Outside", None, None, None, 49, 49),
        ],
    )
    municipality = Municipality(
        "osm-relation-1",
        "07000000",
        "Real",
        6,
        [[[(40, 44), (41, 44), (41, 45), (40, 45), (40, 44)]]],
        "https://example.org",
        "2026-11-11",
        "abc",
        "polygon",
        1,
    )
    observations = [
        MunicipalObservation("settlement", 40.2, 44.2, 100, {"hansen_idx": 1}, True, 1, 0)
    ]
    service.values(municipality, observations)
    service.close()
    values = {value.criterion_id: value for value in service.values(municipality, observations)}
    school = values["N04"]
    assert school.status == "available"
    assert school.thresholds == (500, 800, 1000)
    assert [value.point_share_percent for value in school.values] == [50, 50, 100]
    assert school.reference_points == 2
    assert school.origin_kind == "residential_reference_points"
    assert school.basis_kind == "scenario_reference"
    assert not school.legal_compliance_confirmed
    assert values["N01"].thresholds == (60,)
    assert values["N02"].thresholds == (120,)
    assert road.calls == 1
