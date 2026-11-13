import json
import re
from threading import Lock

from app.domain.errors import DataUnavailable
from app.domain.transit_journey import TransitConnection
from app.repository.clickhouse.client import ClickHouseReader
from app.usecase.transit_catalog import TransitSnapshot, TransitStop


class ClickHouseTransitCatalog:
    def __init__(self, reader: ClickHouseReader, database: str = "plexus_transit") -> None:
        if re.fullmatch(r"[a-z][a-z0-9_]{0,63}", database) is None:
            raise ValueError("Invalid transit database identifier")
        self.database = database
        self.reader = reader
        self.cached: TransitSnapshot | None = None
        self.lock = Lock()

    def latest(self) -> TransitSnapshot:
        with self.lock:
            heads = self.reader.rows(f'SELECT * FROM {self.database}.snapshots ORDER BY published_at DESC,id DESC LIMIT 1', {})
            if not heads:
                raise DataUnavailable('No verified transit snapshot has been published')
            head = heads[0]
            if self.cached is not None and self.cached.id == head['id']:
                return self.cached
            parameters = {'snapshot': str(head['id'])}
            stops = self.reader.rows(f'SELECT * EXCEPT snapshot FROM {self.database}.stops WHERE snapshot={{snapshot:String}} ORDER BY id', parameters)
            connections = self.reader.rows(f'SELECT trip_id,source,target,departure,arrival,sequence FROM {self.database}.connections WHERE snapshot={{snapshot:String}} ORDER BY trip_id,sequence', parameters)
            if len(stops) != head['stop_count'] or len(connections) != head['connection_count']:
                raise DataUnavailable('Published transit snapshot is incomplete')
            metadata = json.loads(head['metadata'])
            result = TransitSnapshot(head['id'], head['source_date'], head['source_url'], head['input_sha256'],
                                     metadata['clock_basis'], metadata['timezone_verified'], metadata['coverage_complete'],
                                     metadata['operating_service_verified'], [TransitStop(**row) for row in stops],
                                     [TransitConnection(**row) for row in connections])
            identifiers = {stop.id for stop in result.stops}
            if any(row.source not in identifiers or row.target not in identifiers for row in result.connections):
                raise DataUnavailable('Transit connection references an absent stop')
            self.cached = result
            return result
