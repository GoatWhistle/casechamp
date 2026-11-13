from app.adapter.transit.factory import TransitWalkingFactory
from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.pedestrian import ClickHousePedestrianRepository
from app.repository.clickhouse.transit import ClickHouseTransitCatalog
from app.repository.clickhouse.transit_locations import ClickHouseTransitLocations
from app.usecase.transit_queries import TransitQueries


def build_transit_queries(reader: ClickHouseReader) -> TransitQueries:
    walking = TransitWalkingFactory(lambda region: ClickHousePedestrianRepository(reader, region),
                                    lambda region: ClickHousePedestrianRepository(reader, region).latest_revision())
    return TransitQueries(ClickHouseTransitCatalog(reader), ClickHouseTransitLocations(reader), walking.for_region)
