import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI

from app.adapter.chat.calculation_tools import CalculationTools
from app.adapter.chat.gateway import CodexResponsesGateway
from app.adapter.chat.municipal_tools import MunicipalTools
from app.adapter.chat.tools import AtlasTools
from app.adapter.log.stdlib import StdlibLogger
from app.adapter.normative.archived_indices import ArchivedIndexMapRepository
from app.adapter.normative.fire_routing import FireRoutingFactory
from app.adapter.normative.regional_walking import RegionalWalkingFactory
from app.adapter.normative.routing import GraphNormativeRouting
from app.adapter.road_analysis.jobs import AnalysisJobs
from app.adapter.road_corridor.resolver import CorridorResolver
from app.adapter.road_graph.jobs import RoadJobs
from app.adapter.road_graph.selection_geometry import SelectionGeometry
from app.adapter.road_stress.jobs import StressJobs
from app.adapter.traffic.indices import TrafficIndices
from app.adapter.traffic.jobs import TrafficJobs
from app.adapter.traffic.municipal_baselines import MunicipalBaselines
from app.adapter.traffic.municipal_connectivity import MunicipalConnectivity
from app.adapter.traffic.municipal_scenarios import MunicipalScenarioJobs
from app.adapter.traffic.municipal_social import MunicipalSocialAccess
from app.atlas_wiring import build_atlas_routers
from app.controller.atlas.accessibility import build_accessibility_router
from app.controller.atlas.airports import build_airports_router
from app.controller.chat.router import build_chat_router
from app.controller.errors import ErrorHandlers
from app.controller.municipalities.access import build_municipal_access_router
from app.controller.municipalities.indices import build_municipal_indices_router
from app.controller.municipalities.router import build_municipality_router
from app.controller.normative.indices import build_regional_indices_router
from app.controller.normative.regional_measurements import build_regional_measurements_router
from app.controller.normative.regional_view import build_regional_view_router
from app.controller.normative.regions import build_regional_catalog_router
from app.controller.road_analysis.router import build_analysis_router
from app.controller.road_graph.compression import RoadGraphCompression
from app.controller.road_graph.router import build_road_graph_router
from app.controller.road_stress.router import build_stress_router
from app.controller.router import build_api_router
from app.controller.scenarios.router import build_scenarios_router
from app.controller.scenarios.sensitivity import build_sensitivity_router
from app.controller.traffic.municipal_scenarios import build_municipal_scenarios_router
from app.controller.traffic.router import build_traffic_router
from app.controller.transit import build_transit_router
from app.municipal_wiring import build_municipal_access, build_municipal_services
from app.normative_wiring import build_pilot_normative_router
from app.repository.clickhouse.accessibility import ClickHouseAccessibilityRepository
from app.repository.clickhouse.airports import ClickHouseAirportRepository
from app.repository.clickhouse.atlas import ClickHouseAtlasRepository
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.graph_snapshot import ClickHouseGraphSnapshot
from app.repository.clickhouse.index_bases import ClickHouseIndexBasisRepository
from app.repository.clickhouse.index_map import ClickHouseIndexMapRepository
from app.repository.clickhouse.municipal_indices import ClickHouseMunicipalIndexRepository
from app.repository.clickhouse.municipalities import ClickHouseMunicipalRepository
from app.repository.clickhouse.pedestrian import ClickHousePedestrianRepository
from app.repository.clickhouse.regional_catalog import ClickHouseRegionalCatalogRepository
from app.repository.clickhouse.regional_measurements import ClickHouseRegionalMeasurementRepository
from app.repository.clickhouse.regional_view import ClickHouseRegionalViewRepository
from app.repository.clickhouse.road_view import ClickHouseRoadView
from app.repository.clickhouse.scenario import ClickHouseScenarioRepository
from app.repository.clickhouse.scenario_indices import ClickHouseScenarioIndexRepository
from app.repository.clickhouse.state import ClickHouseAnalysisStore, ClickHouseRoadJobStore
from app.repository.clickhouse.stress import ClickHouseStressStore
from app.repository.clickhouse.traffic_source import ClickHouseTrafficSource
from app.repository.clickhouse.traffic_state import ClickHouseTrafficStore
from app.settings import Settings, load_settings
from app.transit_wiring import build_transit_queries
from app.usecase.accessibility import AccessibilityQueries
from app.usecase.airports import AirportQueries
from app.usecase.chat import Chat
from app.usecase.chat_calculation_review import CalculationReviews
from app.usecase.links import LinkQueries
from app.usecase.municipal_indices import MunicipalIndexQueries
from app.usecase.municipal_social import MunicipalSocialSources
from app.usecase.municipalities import MunicipalityQueries
from app.usecase.normative.index_map import IndexMapQueries
from app.usecase.normative.indices import RegionalIndices
from app.usecase.normative.regional_catalog import RegionalCatalogQueries
from app.usecase.normative.regional_measurements import RegionalMeasurements
from app.usecase.normative.regional_view import RegionalViewQueries
from app.usecase.reference import ReferenceQueries
from app.usecase.regions import RegionQueries
from app.usecase.road_analysis import RoadAnalysis
from app.usecase.road_corridor import RoadCorridors
from app.usecase.road_graph import RoadGraph
from app.usecase.scenarios import ScenarioQueries, ScenarioRepository
from app.usecase.search import Search
from app.usecase.sensitivity import AccessibilitySensitivity
from app.usecase.settlements import SettlementQueries


def create_app(settings: Settings | None = None, *, scenario_repository: ScenarioRepository | None = None) -> FastAPI:
    config = settings or load_settings(os.environ)
    reader = ClickHouseReader(config.clickhouse_url or "http://127.0.0.1:18123",
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
    municipal_queries = MunicipalityQueries(ClickHouseMunicipalRepository(reader), atlas)
    walking = RegionalWalkingFactory(
        lambda region: ClickHousePedestrianRepository(normative_reader, region),
        lambda region: ClickHousePedestrianRepository(normative_reader, region).latest_revision(),
    )
    municipal_services = build_municipal_services(
        normative_reader, config.municipal_dataset, regional_catalog, normative_routing, walking,
    )
    transit = build_transit_queries(normative_reader)
    municipal_access = build_municipal_access(normative_reader, config.municipal_dataset, regional_catalog, municipal_queries)
    road_view = ClickHouseRoadView(reader.url, config.clickhouse_user, config.clickhouse_password)
    geometry = SelectionGeometry(road_jobs.data) if road_jobs else None
    road_graph = RoadGraph(road_jobs, atlas, road_view, geometry)
    analysis_jobs = (
        AnalysisJobs(road_jobs, ClickHouseAnalysisStore(reader))
        if road_jobs and config.graph_dir
        else None
    )
    analysis = RoadAnalysis(analysis_jobs, atlas)
    corridors = RoadCorridors(CorridorResolver(road_jobs) if road_jobs else None)
    stress = StressJobs(road_jobs, ClickHouseStressStore(reader)) if road_jobs else None
    geography = config.traffic_geography
    if geography is None and config.graph_dir:
        archive = config.graph_dir.parent / "traffic-geography-national"
        pilot = config.graph_dir.parent / "traffic-geography" / "geography.json"
        geography = archive if any(archive.glob("tiles/*/geography.npz")) else pilot if pilot.is_file() else None
    traffic = (TrafficJobs(ClickHouseTrafficSource(reader), ClickHouseTrafficStore(reader), config.graph_dir,
                              TrafficIndices(road_jobs.data),
                              geography=geography, workers=config.traffic_workers)
               if config.graph_dir and road_jobs else None)
    municipal_baselines = MunicipalBaselines(config.graph_dir.parent / "municipal-traffic-baselines", municipal_queries, road_jobs.data if road_jobs else None) if config.graph_dir else None
    municipal_connectivity = MunicipalConnectivity(road_jobs.data, municipal_baselines, ClickHouseMunicipalIndexRepository(reader)) if road_jobs and municipal_baselines else None
    municipal_scenarios = MunicipalScenarioJobs(municipal_baselines.directory, ClickHouseTrafficStore(reader), municipal_baselines, municipal_connectivity, MunicipalSocialAccess(MunicipalSocialSources(municipal_access))) if municipal_baselines else None
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
                    sensitivity, road_graph if road_jobs else None, analysis, corridors, stress, traffic,
                    MunicipalTools(MunicipalIndexQueries(municipal_queries, ClickHouseMunicipalIndexRepository(reader), municipal_services), municipal_scenarios, municipal_access, transit)
                ),
                road_graph if road_jobs else None,
                corridors,
            )
        )
        if config.chat_enabled
        else None
    )

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        yield
        municipal_services.close()
        if municipal_scenarios is not None:
            municipal_scenarios.close()
        if traffic is not None:
            traffic.close()
        if stress is not None:
            stress.close()
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
            *build_atlas_routers(atlas, config.contextual_boundaries, config.contextual_water),
            build_airports_router(AirportQueries(ClickHouseAirportRepository(atlas), atlas)),
            build_accessibility_router(AccessibilityQueries(ClickHouseAccessibilityRepository(reader), atlas)),
            build_scenarios_router(scenarios),
            build_regional_catalog_router(regional_catalog),
            build_municipality_router(municipal_queries),
            build_municipal_access_router(municipal_access),
            build_transit_router(transit),
            build_municipal_indices_router(MunicipalIndexQueries(
                municipal_queries, ClickHouseMunicipalIndexRepository(reader), municipal_services
            )),
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
                    archive=ArchivedIndexMapRepository(config.normative_archive),
                ),
            ),
            build_regional_measurements_router(
                RegionalMeasurements(
                    regional_catalog,
                    ClickHouseRegionalMeasurementRepository(normative_reader),
                    normative_routing,
                    lambda: datetime.now(UTC),
                    walking=walking,
                    fire=FireRoutingFactory(road_jobs.delta.base) if road_jobs else None,
                    views=regional_views,
                )
            ),
            build_pilot_normative_router(normative_reader, normative_routing, road_jobs.delta.base if road_jobs else None),
            build_sensitivity_router(sensitivity),
            build_chat_router(Chat(gateway, analysis, CalculationReviews(road_graph, stress, corridors, traffic, municipal_scenarios))),
        )
    )
    app.include_router(build_road_graph_router(road_graph), prefix="/api/v1")
    app.include_router(build_analysis_router(analysis), prefix="/api/v1")
    app.include_router(build_stress_router(stress), prefix="/api/v1")
    app.include_router(build_traffic_router(traffic), prefix="/api/v1")
    app.include_router(build_municipal_scenarios_router(municipal_scenarios), prefix="/api/v1")
    return app
