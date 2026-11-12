import json
from datetime import UTC, datetime
from hashlib import sha256
from io import BytesIO
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq
from analytics.client import ClickHouse
from pyarrow import ipc


def bounds_filter(bounds: list[float], alias: str = "") -> str:
    if (
        len(bounds) != 4
        or any(not np.isfinite(v) for v in bounds)
        or not -180 <= bounds[0] < bounds[2] <= 180
        or not -90 <= bounds[1] < bounds[3] <= 90
    ):
        raise ValueError("Use west,south,east,north with ordered geographic bounds")
    west, south, east, north = bounds
    return f"{alias}lon BETWEEN {west} AND {east} AND {alias}lat BETWEEN {south} AND {north}"


def export_snapshot(destination: Path, bounds: list[float] | None) -> None:
    if destination.exists():
        raise ValueError("Snapshot output exists; choose a new directory")
    destination.mkdir(parents=True)
    client = ClickHouse()
    revision_query = "SELECT key,value FROM plexus_atlas.atlas_metadata WHERE key IN ('graph_revision','road_cost_model_version') ORDER BY key"
    before = client.rows(revision_query)
    nodes = (
        f"SELECT node FROM plexus_graph.nodes WHERE {bounds_filter(bounds)}"
        if bounds
        else ""
    )
    restriction = f"AND e.src IN ({nodes}) AND e.dst IN ({nodes})" if bounds else ""
    columns = {row["name"] for row in client.rows("DESCRIBE TABLE plexus_graph.ways")}
    season = "AND w.operating_season='all'" if "operating_season" in columns else ""
    query = f"""SELECT e.src AS src,e.dst AS dst,e.km AS km,w.way_id AS way_id,
        e.km / c.freeflow_speed_kmh AS free_hours,c.capacity_pcu_h AS capacity,
        c.lane_basis LIKE '%shared%' AS shared,
        w.highway IN ('residential','living_street','unclassified','service','tertiary','tertiary_link') AS access
        FROM plexus_graph.edges e
        INNER JOIN plexus_graph.ways w ON e.way_idx=w.way_idx
        INNER JOIN plexus_graph.road_costs c ON c.way_idx=e.way_idx
        WHERE NOT c.is_ferry AND c.capacity_pcu_h>0 AND c.freeflow_speed_kmh>0
        AND e.km>0 {season} {restriction}
        ORDER BY e.src,e.dst,w.way_id"""
    for name, sql in [
        ("edges", query),
        (
            "nodes",
            "SELECT node,lat,lon FROM plexus_graph.nodes"
            + (f" WHERE {bounds_filter(bounds)}" if bounds else "")
            + " ORDER BY node",
        ),
        (
            "places",
            "SELECT point_id,settlement,region,population,node,lat,lon FROM plexus_graph.locations"
            + (f" WHERE {bounds_filter(bounds)}" if bounds else "")
            + " ORDER BY point_id",
        ),
    ]:
        print(f"Exporting {name}", flush=True)
        table = ipc.open_stream(
            BytesIO(client.request(sql + " FORMAT ArrowStream"))
        ).read_all()
        pq.write_table(table, destination / f"{name}.parquet")
    metadata = client.rows(revision_query)
    if before != metadata:
        raise ValueError(
            "Graph revision changed during export; create a fresh snapshot"
        )
    import_record(destination, bounds, metadata)


def import_record(
    destination: Path, bounds: list[float] | None, metadata: list[dict]
) -> None:

    (destination / "source.json").write_text(
        json.dumps(
            {
                "bounds": bounds,
                "created_at": datetime.now(UTC).isoformat(),
                "metadata": metadata,
                "sha256": {
                    p.name: sha256(p.read_bytes()).hexdigest()
                    for p in destination.glob("*.parquet")
                },
                "network": "original_directed_edges_conservative_directional_capacity",
                "limits": [
                    "No intersection or turning capacity",
                    "Shared single lane combines both directions",
                    "Asymmetric lane counts use conservative representative capacity",
                    "Bounds clip network; no external transit inferred",
                ],
            },
            ensure_ascii=False,
            indent=2,
        )
    )
