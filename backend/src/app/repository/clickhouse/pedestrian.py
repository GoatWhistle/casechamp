from app.domain.errors import DataUnavailable
from app.repository.clickhouse.client import ClickHouseReader
from app.usecase.normative.walking import PedestrianNetwork

NETWORK = """SELECT revision,source_url,source_timestamp,node_count,edge_count
FROM plexus_normative.pedestrian_networks
WHERE ({revision:String}='' OR revision={revision:String})
AND revision IN (SELECT revision FROM plexus_normative.pedestrian_regions
                WHERE region_id={region:String} AND purpose={purpose:String})
ORDER BY created_at DESC LIMIT 1"""
NODES = """SELECT node_index,latitude,longitude FROM plexus_normative.pedestrian_nodes
WHERE revision={revision:String} ORDER BY node_index"""
EDGES = """SELECT source,target,metres,way_id FROM plexus_normative.pedestrian_edges
WHERE revision={revision:String} ORDER BY source,target,way_id"""


class ClickHousePedestrianRepository:
    def __init__(self, reader: ClickHouseReader, region_id: str, purpose: str = "physical") -> None:
        self.reader = reader
        self.region_id = region_id
        self.purpose = purpose

    def network(self, revision: str | None = None) -> PedestrianNetwork:
        found = self.reader.rows(
            NETWORK, {"revision": revision or "", "region": self.region_id, "purpose": self.purpose}
        )
        if not found:
            raise DataUnavailable("No completed pedestrian network has been imported")
        meta = found[0]
        params = {"revision": str(meta["revision"])}
        nodes = self.reader.arrow(NODES, params).to_pydict()
        edges = self.reader.arrow(EDGES, params).to_pydict()
        if (
            len(nodes["node_index"]) != meta["node_count"]
            or len(edges["source"]) != meta["edge_count"]
        ):
            raise DataUnavailable("Pedestrian network snapshot is incomplete")
        return PedestrianNetwork(
            meta["revision"],
            list(zip(nodes["node_index"], nodes["latitude"], nodes["longitude"], strict=True)),
            list(
                zip(edges["source"], edges["target"], edges["metres"], edges["way_id"], strict=True)
            ),
            meta["source_url"],
            meta["source_timestamp"],
        )
