from dataclasses import replace
from typing import cast
from unittest.mock import Mock

import pytest
from tests.unit.domain.normative.fire_evidence.factories import facility

from app.domain.errors import InvalidQuery
from app.usecase.normative.regional_catalog import RegionalCatalogQueries, RegionalCatalogRepository


def test_generic_regional_objects_are_not_verified_clinical_forms_or_calculations() -> None:
    repository = Mock(spec=RegionalCatalogRepository)
    repository.region_name.return_value = "Other region"
    repository.candidates.return_value = [replace(facility(), service="medical")]
    result = RegionalCatalogQueries(cast(RegionalCatalogRepository, repository)).catalog("R", "N01")
    assert result.region_name == "Other region"
    assert result.category == "medical"
    assert result.candidate_count == 1
    assert result.calculation_available is False
    assert result.profile_verification == "unconfirmed"
    assert result.facilities[0].service == "medical"
    repository.candidates.assert_called_once_with("R", "medical")


@pytest.mark.parametrize("criterion,name", [("N99", "Region"), ("N01", None)])
def test_unknown_regional_catalogs_fail_without_returning_another_region(
    criterion: str, name: str | None
) -> None:
    repository = Mock(spec=RegionalCatalogRepository)
    repository.region_name.return_value = name
    with pytest.raises(InvalidQuery):
        RegionalCatalogQueries(cast(RegionalCatalogRepository, repository)).catalog(
            "unknown", criterion
        )
    repository.candidates.assert_not_called()


def test_routing_catalog_keeps_origin_region_but_accepts_cross_border_targets() -> None:
    repository = Mock(spec=RegionalCatalogRepository)
    repository.region_name.return_value = "Origin region"
    nearby = replace(facility(), id="neighbor-hospital", service="medical")
    repository.routing_candidates.return_value = [nearby]
    result = RegionalCatalogQueries(cast(RegionalCatalogRepository, repository)).catalog(
        "origin", "N01", cross_region=True
    )
    assert result.region_id == "origin"
    assert result.facilities == [nearby]
    assert result.profile_verification == "unconfirmed"
    repository.routing_candidates.assert_called_once_with("medical")
    repository.candidates.assert_not_called()
