import json

from app.domain.errors import DataUnavailable
from app.repository.clickhouse.client import ClickHouseReader
from app.usecase.municipalities import Municipality


class ClickHouseMunicipalRepository:
    def __init__(self, reader: ClickHouseReader) -> None:
        self.reader = reader

    def boundaries(self, region_id: str) -> list[Municipality]:
        rows = self.reader.rows(
            "SELECT id,region_id,name,admin_level,geometry_json,source_url,observed_at,"
            "source_sha256,region_assignment,region_overlap_fraction "
            "FROM plexus_atlas.municipal_boundaries FINAL "
            "WHERE region_id={region:String} ORDER BY name,id",
            {"region": region_id},
        )
        result = []
        try:
            for row in rows:
                geometry = json.loads(row.pop("geometry_json"))
                if geometry["type"] != "MultiPolygon" or not geometry["coordinates"]:
                    raise ValueError("Municipal geometry must be a nonempty MultiPolygon")
                coordinates = [
                    [[(float(lon), float(lat)) for lon, lat in ring] for ring in polygon]
                    for polygon in geometry["coordinates"]
                ]
                result.append(Municipality(coordinates=coordinates, **row))
        except (ValueError, TypeError, KeyError) as error:
            raise DataUnavailable("Stored municipal geometry is invalid") from error
        return result
