from collections import OrderedDict
from threading import Lock
from time import monotonic

from app.domain.municipal_metrics import MunicipalObservation
from app.repository.clickhouse.client import ClickHouseReader
from app.usecase.municipal_indices import MunicipalIndexSource

METRICS = (
    "hansen_idx",
    "hansen_1h",
    "hansen_2h",
    "hansen_4h",
    "remoteness_ca",
    "aria",
    "harris",
    "t_city50k_best_h",
    "rai_2km",
)


class ClickHouseMunicipalIndexRepository:
    def __init__(self, reader: ClickHouseReader) -> None:
        self.reader = reader
        self._cache: OrderedDict[tuple[str, str], tuple[float, MunicipalIndexSource]] = (
            OrderedDict()
        )
        self._lock = Lock()

    def points(self, region_id: str, season: str) -> MunicipalIndexSource:
        key = (region_id, season)
        with self._lock:
            cached = self._cache.get(key)
            if cached and monotonic() - cached[0] < 60:
                self._cache.move_to_end(key)
                return cached[1]
        rows = self.reader.rows(
            "SELECT n.point_id,p.lon,p.lat,n.population,n.is_rural,p.node,p.snap_km,"
            + ",".join("n." + metric for metric in METRICS)
            + " FROM plexus_casechamp.idx_np n INNER JOIN plexus_graph.points p "
            "ON n.point_id=p.point_id AND n.region=p.region "
            "WHERE n.season={season:String} AND n.region IN "
            "(SELECT region FROM plexus_graph.region_codes WHERE oktmo={region:String}) "
            "AND p.lon IS NOT NULL AND p.lat IS NOT NULL ORDER BY n.point_id",
            {"region": region_id, "season": season},
        )
        metadata = {
            row["key"]: row["value"]
            for row in self.reader.rows(
                "SELECT key,value FROM plexus_atlas.atlas_metadata WHERE key IN "
                "('model_version','index_model_version','index_artifact_version','artifact_version','road_cost_model_version')",
                {},
            )
        }
        result = MunicipalIndexSource(
            [
                MunicipalObservation(
                    str(row["point_id"]),
                    float(row["lon"]),
                    float(row["lat"]),
                    int(row["population"]) if row["population"] is not None else None,
                    {
                        metric: float(row[metric]) if row[metric] is not None else None
                        for metric in METRICS
                    },
                    bool(row["is_rural"]),
                    int(row["node"]) if row["node"] is not None else None,
                    float(row["snap_km"]) if row["snap_km"] is not None else None,
                )
                for row in rows
            ],
            metadata.get("index_model_version") or metadata.get("model_version"),
            metadata.get("artifact_version") or metadata.get("index_artifact_version"),
            "plexus_casechamp.idx_np",
        )
        with self._lock:
            self._cache[key] = (monotonic(), result)
            self._cache.move_to_end(key)
            while len(self._cache) > 12:
                self._cache.popitem(last=False)
        return result
