from app.domain.errors import DataUnavailable
from app.repository.clickhouse.client import ClickHouseReader
from app.usecase.transit_queries import TransitPlace


class ClickHouseTransitLocations:
    def __init__(self, reader: ClickHouseReader) -> None:
        self.reader = reader

    def origin(self, region: str, identifier: str, revision: str) -> TransitPlace:
        rows = self.reader.rows(
            "SELECT id,name,latitude,longitude FROM plexus_normative.pedestrian_origins "
            "WHERE revision={revision:String} AND id={id:String} AND revision IN "
            "(SELECT revision FROM plexus_normative.pedestrian_regions WHERE region_id={region:String} AND purpose='physical') LIMIT 1",
            {'revision': revision, 'id': identifier, 'region': region},
        )
        if rows:
            return TransitPlace(**rows[0], coordinate_status='residential_reference_not_entrance')
        rows = self.reader.rows(
            "SELECT id,name,latitude,longitude FROM plexus_normative.regional_origin_points FINAL "
            "WHERE region_id={region:String} AND id={id:String} AND snapshot=("
            "SELECT revision FROM plexus_normative.regional_origin_snapshots "
            "WHERE graph_revision=(SELECT value FROM plexus_atlas.atlas_metadata WHERE key='graph_revision') "
            "ORDER BY created_at DESC LIMIT 1) LIMIT 1", {'region': region, 'id': identifier},
        )
        if not rows:
            raise DataUnavailable('Reference point is absent from the selected region')
        return TransitPlace(**rows[0], coordinate_status='settlement_reference_not_entrance')

    def facility(self, region: str, identifier: str) -> TransitPlace:
        rows = self.reader.rows(
            "SELECT id,name,latitude,longitude FROM plexus_normative.national_inventory FINAL "
            "WHERE region_id={region:String} AND id={id:String} LIMIT 1", {'region': region, 'id': identifier},
        )
        if rows:
            return TransitPlace(**rows[0], coordinate_status='osm_institution_pin')
        rows = self.reader.rows(
            "SELECT f.id,f.name,f.latitude,f.longitude,f.coordinate_status FROM plexus_normative.facilities f "
            "INNER JOIN plexus_normative.regional_directory_memberships m ON f.id=m.facility_id AND f.service=m.service "
            "WHERE m.region_id={region:String} AND f.id={id:String} LIMIT 1", {'region': region, 'id': identifier},
        )
        if not rows:
            raise DataUnavailable('Facility is absent from the selected region catalog')
        return TransitPlace(**rows[0])
