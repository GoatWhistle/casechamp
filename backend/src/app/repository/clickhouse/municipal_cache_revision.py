import json
from hashlib import sha256
from pathlib import Path

from app.domain.errors import DataUnavailable
from app.repository.clickhouse.client import ClickHouseReader


class MunicipalCacheRevision:
    def __init__(self, reader: ClickHouseReader, dataset: Path, baselines: Path) -> None:
        self.reader, self.dataset, self.baselines = reader, dataset, baselines
        self._database_revision: str | None = None

    def __call__(self) -> str:
        parts = self.reader.rows(
            "SELECT database,table,partition_id,sum(rows) AS rows,max(max_block_number) AS newest_block, max(data_version) AS mutation FROM system.parts "
            "WHERE active AND ((database='plexus_casechamp' AND table='idx_np') "
            "OR database='plexus_graph' OR (database='plexus_normative' AND table IN ("
            "'facilities','inventory_regions','national_inventory','regional_directory_memberships',"
            "'service_directories','regional_measurements','regional_origin_points',"
            "'regional_origin_snapshots','pedestrian_networks','pedestrian_regions',"
            "'pedestrian_nodes','pedestrian_edges')) "
            "OR (database='plexus_atlas' AND table IN ('municipal_boundaries','atlas_metadata','regions'))) "
            "GROUP BY database,table,partition_id ORDER BY database,table,partition_id", {},
        )
        if not parts:
            raise DataUnavailable('Municipal cache source revision is unavailable')
        digest = sha256(json.dumps(parts, sort_keys=True, default=str).encode())
        current = digest.hexdigest()
        if self._database_revision is not None and self._database_revision != current:
            raise DataUnavailable('Source snapshots changed; reload the service before reading municipal caches')
        self._database_revision = current
        for namespace, (root, pattern) in enumerate([(self.dataset, 'published/*.json'), (self.baselines, '*/sha256')]):
            for path in sorted(root.glob(pattern)):
                digest.update((str(namespace) + '/' + str(path.relative_to(root))).encode())
                digest.update(path.read_bytes())
        return digest.hexdigest()
