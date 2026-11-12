import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import APIRouter, FastAPI

from app.adapter.chat.calculation_tools import CalculationTools
from app.adapter.chat.gateway import CodexResponsesGateway
from app.adapter.chat.tools import AtlasTools
from app.adapter.log.stdlib import StdlibLogger
from app.adapter.normative.fire_routing import FireRoutingFactory
from app.adapter.normative.origin_attachment import GraphOriginAttachment
from app.adapter.normative.regional_walking import RegionalWalkingFactory
from app.adapter.normative.routing import GraphNormativeRouting
from app.adapter.normative.walking_routing import WalkingNormativeRouting
from app.adapter.road_analysis.jobs import AnalysisJobs
from app.adapter.road_corridor.resolver import CorridorResolver
from app.adapter.road_graph.jobs import RoadJobs
from app.controller.atlas.accessibility import build_accessibility_router
from app.controller.atlas.airports import build_airports_router
from app.controller.atlas.catalog import build_catalog_router
from app.controller.atlas.regions import build_regions_router
from app.controller.chat.router import build_chat_router
from app.controller.errors import ErrorHandlers
from app.controller.normative.indices import build_regional_indices_router
from app.controller.normative.regional_measurements import build_regional_measurements_router
from app.controller.normative.regional_view import build_regional_view_router
from app.controller.normative.regions import build_regional_catalog_router
from app.controller.normative.router import build_normative_router
from app.controller.road_analysis.router import build_analysis_router
from app.controller.road_graph.compression import RoadGraphCompression
from app.controller.road_graph.router import build_road_graph_router
from app.controller.router import build_api_router
from app.controller.scenarios.router import build_scenarios_router
from app.controller.scenarios.sensitivity import build_sensitivity_router
from app.repository.clickhouse.accessibility import ClickHouseAccessibilityRepository
from app.repository.clickhouse.airports import ClickHouseAirportRepository
from app.repository.clickhouse.atlas import ClickHouseAtlasRepository
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.graph_snapshot import ClickHouseGraphSnapshot
from app.repository.clickhouse.index_bases import ClickHouseIndexBasisRepository
from app.repository.clickhouse.index_map import ClickHouseIndexMapRepository
from app.repository.clickhouse.normative import ClickHouseNormativeRepository
from app.repository.clickhouse.pedestrian import ClickHousePedestrianRepository
from app.repository.clickhouse.regional_catalog import ClickHouseRegionalCatalogRepository
from app.repository.clickhouse.regional_measurements import ClickHouseRegionalMeasurementRepository
from app.repository.clickhouse.regional_view import ClickHouseRegionalViewRepository
from app.repository.clickhouse.road_view import ClickHouseRoadView
from app.repository.clickhouse.scenario import ClickHouseScenarioRepository
from app.repository.clickhouse.scenario_indices import ClickHouseScenarioIndexRepository
from app.repository.clickhouse.state import ClickHouseAnalysisStore, ClickHouseRoadJobStore
from app.settings import Settings, load_settings
from app.usecase.accessibility import AccessibilityQueries
from app.usecase.airports import AirportQueries
from app.usecase.chat import Chat
from app.usecase.interface import AtlasRepository
from app.usecase.links import LinkQueries
from app.usecase.normative.index_map import IndexMapQueries
from app.usecase.normative.indices import RegionalIndices
from app.usecase.normative.queries import NormativeQueries
from app.usecase.normative.regional_catalog import RegionalCatalogQueries
from app.usecase.normative.regional_measurements import RegionalMeasurements
from app.usecase.normative.regional_view import RegionalViewQueries
from app.usecase.overview import OverviewQuery
from app.usecase.reference import ReferenceQueries
from app.usecase.regions import RegionQueries
from app.usecase.road_analysis import RoadAnalysis
from app.usecase.road_corridor import RoadCorridors
from app.usecase.road_graph import RoadGraph
from app.usecase.scenarios import ScenarioQueries, ScenarioRepository
from app.usecase.search import Search
from app.usecase.sensitivity import AccessibilitySensitivity
from app.usecase.settlements import SettlementQueries


def build_atlas_routers(repository: AtlasRepository) -> list[APIRouter]:
    return [
        build_catalog_router(
            OverviewQuery(repository), ReferenceQueries(repository), Search(repository)
        ),
        build_regions_router(
            RegionQueries(repository), LinkQueries(repository), SettlementQueries(repository)
        ),
    ]


def create_app(
    settings: Settings | None = None, *, scenario_repository: ScenarioRepository | None = None
) -> FastAPI:
    config = settings or load_settings(os.environ)
    reader = ClickHouseReader(
        config.clickhouse_url or "http://127.0.0.1:18123",
        config.clickhouse_user,
        config.clickhouse_password,
    )
    atlas = ClickHouseAtlasRepository(reader)
    normative_reader = ClickHouseReader(
        reader.url,
        config.clickhouse_user,
        config.clickhouse_password,
        max_threads=1,
        max_block_size=8192,
    )
    road_jobs = (
        RoadJobs(
            config.graph_dir,
            ClickHouseGraphSnapshot(normative_reader),
            ClickHouseRoadJobStore(reader),
            config.road_workers,
        )
        if config.graph_dir
        else None
    )
    normative_routing = GraphNormativeRouting(road_jobs.delta.base) if road_jobs else None
    regional_views = ClickHouseRegionalViewRepository(normative_reader)
    regional_catalog = RegionalCatalogQueries(ClickHouseRegionalCatalogRepository(normative_reader))
    road_view = ClickHouseRoadView(reader.url, config.clickhouse_user, config.clickhouse_password)
    road_graph = RoadGraph(road_jobs, atlas, road_view)
    analysis_jobs = (
        AnalysisJobs(road_jobs, ClickHouseAnalysisStore(reader))
        if road_jobs and config.graph_dir
        else None
    )
    analysis = RoadAnalysis(analysis_jobs, atlas)
    corridors = RoadCorridors(CorridorResolver(road_jobs) if road_jobs else None)
    sensitivity = AccessibilitySensitivity(atlas)
    scenarios = ScenarioQueries(scenario_repository or ClickHouseScenarioRepository(reader))
    gateway = (
        CodexResponsesGateway(
            AtlasTools(
                RegionQueries(atlas),
                LinkQueries(atlas),
                SettlementQueries(atlas),
                Search(atlas),
                ReferenceQueries(atlas),
                CalculationTools(
                    sensitivity, road_graph if road_jobs else None, analysis, corridors
                ),
            )
        )
        if config.chat_enabled
        else None
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        yield
        if analysis_jobs is not None:
            analysis_jobs.close()
        if road_jobs is not None:
            road_jobs.close()
        if gateway is not None:
            await gateway.close()

    app = FastAPI(title="Plexus API", version="1.0.0", lifespan=lifespan)
    app.add_middleware(RoadGraphCompression, minimum_size=1000, compresslevel=3)
    app.state.atlas = atlas
    ErrorHandlers(StdlibLogger("app")).register(app)
    app.include_router(
        build_api_router(
            *build_atlas_routers(atlas),
            build_airports_router(AirportQueries(ClickHouseAirportRepository(atlas), atlas)),
            build_accessibility_router(
                AccessibilityQueries(ClickHouseAccessibilityRepository(reader), atlas)
            ),
            build_scenarios_router(scenarios),
            build_regional_catalog_router(regional_catalog),
            build_regional_view_router(RegionalViewQueries(regional_views, regional_catalog)),
            build_regional_indices_router(
                RegionalIndices(
                    ClickHouseIndexBasisRepository(normative_reader),
                    ClickHouseRegionalMeasurementRepository(normative_reader),
                    ClickHouseIndexMapRepository(normative_reader),
                    ClickHouseScenarioIndexRepository(normative_reader),
                ),
                IndexMapQueries(
                    ClickHouseIndexMapRepository(normative_reader),
                    lambda: datetime.now(UTC),
                    ClickHouseScenarioIndexRepository(normative_reader),
                ),
            ),
            build_regional_measurements_router(
                RegionalMeasurements(
                    regional_catalog,
                    ClickHouseRegionalMeasurementRepository(normative_reader),
                    normative_routing,
                    lambda: datetime.now(UTC),
                    walking=RegionalWalkingFactory(
                        lambda region: ClickHousePedestrianRepository(normative_reader, region)
                    ),
                    fire=FireRoutingFactory(road_jobs.delta.base) if road_jobs else None,
                    views=regional_views,
                )
            ),
            build_normative_router(
                NormativeQueries(
                    ClickHouseNormativeRepository(normative_reader),
                    normative_routing,
                    WalkingNormativeRouting(
                        ClickHousePedestrianRepository(normative_reader, "37000000", "pilot")
                    ),
                    FireRoutingFactory(road_jobs.delta.base) if road_jobs else None,
                    clock=lambda: datetime.now(UTC),
                    object_attachment=GraphOriginAttachment(road_jobs.delta.base)
                    if road_jobs
                    else None,
                )
            ),
            build_sensitivity_router(sensitivity),
            build_chat_router(Chat(gateway, analysis)),
        )
    )
    app.include_router(build_road_graph_router(road_graph), prefix="/api/v1")
    app.include_router(build_analysis_router(analysis), prefix="/api/v1")
    return app
