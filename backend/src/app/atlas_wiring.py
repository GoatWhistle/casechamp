from pathlib import Path

from fastapi import APIRouter

from app.adapter.atlas.outside_mask import AtlasOutsideMask
from app.controller.atlas.catalog import build_catalog_router
from app.controller.atlas.regions import build_regions_router
from app.repository.files.contextual_boundaries import JsonContextualBoundaryRepository
from app.repository.files.contextual_water import JsonContextualWaterRepository
from app.usecase.interface import AtlasRepository
from app.usecase.links import LinkQueries
from app.usecase.overview import OverviewQuery
from app.usecase.reference import ReferenceQueries
from app.usecase.regions import RegionQueries
from app.usecase.search import Search
from app.usecase.settlements import SettlementQueries


def build_atlas_routers(
    repository: AtlasRepository, contextual_path: Path, water_path: Path
) -> list[APIRouter]:
    return [
        build_catalog_router(
            OverviewQuery(repository),
            ReferenceQueries(
                repository,
                AtlasOutsideMask(),
                JsonContextualBoundaryRepository(contextual_path),
                JsonContextualWaterRepository(water_path),
            ),
            Search(repository),
        ),
        build_regions_router(
            RegionQueries(repository), LinkQueries(repository), SettlementQueries(repository)
        ),
    ]
