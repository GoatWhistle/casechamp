from pathlib import Path

from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.municipal_published import ClickHouseMunicipalPublished
from app.repository.clickhouse.regional_measurements import ClickHouseRegionalMeasurementRepository
from app.repository.files.municipal_dataset import JsonMunicipalDataset
from app.usecase.municipal_services import MunicipalServiceQueries
from app.usecase.normative.interface import NormativeRouting
from app.usecase.normative.regional_catalog import RegionalCatalogQueries
from app.usecase.normative.regional_models import RegionalWalkingModels


def build_municipal_services(
    reader: ClickHouseReader,
    path: Path,
    catalog: RegionalCatalogQueries,
    road: NormativeRouting | None,
    walking: RegionalWalkingModels,
) -> MunicipalServiceQueries:
    dataset = JsonMunicipalDataset(path)
    published = ClickHouseMunicipalPublished(reader, dataset, catalog)
    return MunicipalServiceQueries(
        catalog,
        road,
        walking,
        ClickHouseRegionalMeasurementRepository(reader).walking_origins,
        published=published.values,
        version=published.version,
    )
