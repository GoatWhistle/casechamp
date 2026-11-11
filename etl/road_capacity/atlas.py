import hashlib
import json

import pyarrow as pa

CASE = "plexus_capacity_casechamp"
ATLAS = "plexus_capacity_atlas"


def rebuild_atlas(store, source, reference):
    rows = store.rows(f"""SELECT c.oktmo region_id,n.season scenario,sum(n.population*n.hansen_idx)/sum(n.population) hansen,
        sumIf(n.population,n.hansen_2h>0) covered_population,sum(n.population) total_population,
        countIf(n.hansen_2h>0) covered_settlements,count() total_settlements,
        sum(n.population*n.hansen_1h)/sum(n.population) hansen_1h,
        sum(n.population*n.hansen_2h)/sum(n.population) hansen_2h,
        sum(n.population*n.hansen_4h)/sum(n.population) hansen_4h
        FROM {CASE}.idx_np n INNER JOIN plexus_capacity_graph.region_codes c ON n.region=c.region
        GROUP BY c.oktmo,n.season ORDER BY n.season,c.oktmo""")
    if len(rows) != 246:
        raise ValueError("Expected 246 legacy atlas index rows")
    artifact = hashlib.sha256(
        json.dumps(
            {"rows": rows, "source": source, "reference": reference}, sort_keys=True
        ).encode()
    ).hexdigest()
    for index, row in enumerate(rows):
        row.update(
            model_version="hansen-release-20261107",
            artifact_version=artifact,
            ordinal=index,
        )
        for field in [
            "covered_population",
            "total_population",
            "covered_settlements",
            "total_settlements",
        ]:
            row[field] = int(row[field])
    for name in ["atlas_indices", "atlas_exported_indices"]:
        target = ATLAS + "." + name
        loading = store.fresh(target)
        store.insert_arrow(loading, pa.Table.from_pylist(rows))
        store.replace(loading, target)
    metadata = store.rows(f"SELECT key,value,ordinal FROM {ATLAS}.atlas_metadata")
    values = {row["key"]: row["value"] for row in metadata}
    values.update(
        road_cost_model_version="road-capacity-v1",
        artifact_version=artifact,
        graph_revision=json.dumps(
            {
                "base": source["source_revision"],
                "road_cost_model": "road-capacity-v1",
                "artifact": artifact,
            },
            sort_keys=True,
        ),
        capacity_reference=json.dumps(reference, sort_keys=True),
        road_cost_unknown_flow="free_flow",
        road_cost_routing_policy=source["routing_policy"],
    )
    target = ATLAS + ".atlas_metadata"
    loading = store.fresh(target)
    store.insert_arrow(
        loading,
        pa.Table.from_pylist(
            [
                {"key": key, "value": value, "ordinal": index}
                for index, (key, value) in enumerate(sorted(values.items()))
            ]
        ),
    )
    store.replace(loading, target)
    return {
        "artifact_version": artifact,
        "regional_rows": len(rows),
        "graph_revision": values["graph_revision"],
    }
