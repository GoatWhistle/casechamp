import json
from collections.abc import Callable
from dataclasses import asdict
from hashlib import sha256
from threading import Lock
from time import monotonic

from app.repository.clickhouse.client import ClickHouseReader
from app.repository.clickhouse.municipal_revision import municipal_road_revision_matches
from app.repository.clickhouse.municipalities import ClickHouseMunicipalRepository
from app.usecase.municipal_dataset import MunicipalDataset, municipal_boundary_digest
from app.usecase.municipal_service_models import MunicipalNormativeValue
from app.usecase.municipalities import Municipality
from app.usecase.normative.regional_catalog import RegionalCatalogQueries


class ClickHouseMunicipalPublished:
    def __init__(
        self,
        reader: ClickHouseReader,
        dataset: MunicipalDataset,
        catalog: RegionalCatalogQueries,
        boundaries: Callable[[str], list[Municipality]] | None = None,
    ) -> None:
        self.reader = reader
        self.dataset = dataset
        self.catalog = catalog
        self.boundaries = boundaries or ClickHouseMunicipalRepository(reader).boundaries
        self._boundary_versions: dict[str, str] = {}
        self._cache: dict[str, tuple[float, dict[str, tuple[str, str]]]] = {}
        self._lock = Lock()

    def _versions(self, region_id: str) -> dict[str, tuple[str, str]]:
        with self._lock:
            cached = self._cache.get(region_id)
            if cached and monotonic() - cached[0] < 5:
                return cached[1]
        heads = self.reader.rows(
            "SELECT criterion_id,argMax(id,tuple(saved_at,id)) AS run_id "
            "FROM plexus_normative.regional_measurements WHERE region_id={region:String} GROUP BY criterion_id",
            {"region": region_id},
        )
        versions = {}
        for head in heads:
            criterion = str(head["criterion_id"])
            facilities = self.catalog.catalog(region_id, criterion).facilities
            digest = sha256(
                json.dumps(
                    [asdict(facility) for facility in facilities], sort_keys=True, allow_nan=False
                ).encode()
            ).hexdigest()
            versions[criterion] = (str(head["run_id"]), digest)
        boundary_digest = municipal_boundary_digest(self.boundaries(region_id))
        with self._lock:
            self._boundary_versions[region_id] = boundary_digest
            if len(self._cache) >= 84:
                self._cache.pop(next(iter(self._cache)))
            self._cache[region_id] = (monotonic(), versions)
        return versions

    def version(self, municipality: Municipality) -> str:
        versions = self._versions(municipality.region_id)
        graph = self.reader.rows(
            "SELECT key,value FROM plexus_atlas.atlas_metadata WHERE key IN ('graph_revision','artifact_version','road_cost_model_version')",
            {},
        )
        walking = self.reader.rows(
            "SELECT n.revision FROM plexus_normative.pedestrian_networks n WHERE n.revision IN (SELECT revision FROM plexus_normative.pedestrian_regions WHERE region_id={region:String} AND purpose='physical') ORDER BY n.created_at DESC LIMIT 1",
            {"region": municipality.region_id},
        )
        return sha256(
            json.dumps(
                (versions, graph, walking, self._boundary_versions.get(municipality.region_id)),
                sort_keys=True,
            ).encode()
        ).hexdigest()

    def values(self, municipality: Municipality) -> list[MunicipalNormativeValue]:
        versions = self._versions(municipality.region_id)
        if self.dataset.find_boundaries(municipality.region_id) != self._boundary_versions.get(
            municipality.region_id
        ):
            return []
        graph_metadata = {
            str(row["key"]): str(row["value"])
            for row in self.reader.rows(
                "SELECT key,value FROM plexus_atlas.atlas_metadata WHERE key IN ('graph_revision','artifact_version','road_cost_model_version')",
                {},
            )
        }
        walking = self.reader.rows(
            "SELECT n.revision FROM plexus_normative.pedestrian_networks n WHERE n.revision IN (SELECT revision FROM plexus_normative.pedestrian_regions WHERE region_id={region:String} AND purpose='physical') ORDER BY n.created_at DESC LIMIT 1",
            {"region": municipality.region_id},
        )
        walking_revision = str(walking[0]["revision"]) if walking else None
        results = []
        for criterion in (f"N{i:02}" for i in range(1, 10)):
            if criterion not in versions:
                continue
            run_id, catalog_digest = versions[criterion]
            source_sha = self.dataset.find_run(
                municipality.region_id, criterion, run_id, "scenario"
            )
            if source_sha is None:
                continue
            source = self.dataset.source(source_sha)
            metadata = json.loads(source.metadata_json)
            if (
                source.graph_revision != walking_revision
                if metadata.get("mode") == "walk"
                else not municipal_road_revision_matches(source.graph_revision, graph_metadata)
            ) or metadata.get("catalog_fingerprint") != catalog_digest:
                continue
            value = self.dataset.existing(source_sha, municipality, criterion)
            if value is not None:
                results.append(value)
        return results
