import argparse
import csv
import json
from datetime import UTC, datetime
from pathlib import Path

import numpy as np

from .storage import CapacityStore

CASE = "plexus_capacity_casechamp"
GRAPH = "plexus_capacity_graph"
ATLAS = "plexus_capacity_atlas"
TABLES = {
    "plexus_graph": ["ways", "edges", "road_lines", "road_costs"],
    "plexus_casechamp": [
        "np_city_times",
        "np_access",
        "idx_np",
        "idx_mo",
        "idx_region",
        "idx_theil",
        "idx_np_gap",
    ],
    "plexus_atlas": ["atlas_indices", "atlas_exported_indices", "atlas_metadata"],
}


def metadata(store, database):
    return {
        r["key"]: r["value"]
        for r in store.rows(f"SELECT key,value FROM {database}.atlas_metadata")
    }


def validate(store, root):
    folder = root / "data/road-capacity"
    state = json.loads((folder / "state.json").read_text())
    if set(state["stages"]) != {"weights", "matrices", "indices", "atlas"}:
        raise ValueError("All four capacity stages must finish before validation")
    source = state["source"]
    active = metadata(store, "plexus_atlas")
    candidate = metadata(store, ATLAS)
    if active["graph_revision"] != source["source_revision"]:
        raise ValueError("Active graph changed since the capacity snapshot")
    if candidate.get("road_cost_model_version") != "road-capacity-v1":
        raise ValueError("Candidate road-cost metadata is missing")
    if candidate["artifact_version"] != state["stages"]["atlas"]["artifact_version"]:
        raise ValueError("Candidate artifact does not match the completed calculation")
    checks = {}

    def check(name, query):
        value = int(store.rows(query)[0]["n"])
        checks[name] = value
        if value:
            raise ValueError(f"Capacity validation failed: {name}: {value}")

    for table in ["ways", "edges", "road_lines"]:
        check(
            "graph_count_" + table,
            f"SELECT abs((SELECT count() FROM {GRAPH}.{table})-(SELECT count() FROM plexus_graph.{table})) n",
        )
    check(
        "edge_topology",
        f"SELECT abs((SELECT groupBitXor(cityHash64(src,dst,way_idx,km)) FROM {GRAPH}.edges)-(SELECT groupBitXor(cityHash64(src,dst,way_idx,km)) FROM plexus_graph.edges)) n",
    )
    check(
        "point_inputs",
        f"SELECT (SELECT groupBitXor(cityHash64(tuple(season,point_id,region,name,population,is_rural,is_dc,on_road,manual_only,no_all_season_road,km_allseason_road,rai_2km))) FROM {CASE}.idx_np)!=(SELECT groupBitXor(cityHash64(tuple(season,point_id,region,name,population,is_rural,is_dc,on_road,manual_only,no_all_season_road,km_allseason_road,rai_2km))) FROM {CASE}.reference_idx_np) n",
    )
    check(
        "free_flow_policy",
        f"SELECT count() n FROM {GRAPH}.road_costs WHERE NOT flow_verified AND (flow_basis!='unknown_free_flow' AND NOT is_ferry OR abs(effective_speed_kmh-freeflow_speed_kmh)>1e-9)",
    )
    check(
        "edge_costs",
        f"SELECT count() n FROM {GRAPH}.edges e INNER JOIN {GRAPH}.road_costs c USING(way_idx) WHERE abs(e.h-CAST(e.km/c.effective_speed_kmh,'Float32'))>1e-7 OR NOT isFinite(e.h) OR e.h<0",
    )
    check(
        "invalid_indices",
        f"SELECT count() n FROM {CASE}.idx_np WHERE NOT isFinite(hansen_idx) OR hansen_idx<0 OR NOT isFinite(aria) OR aria<0 OR aria>15 OR remoteness_ca<0 OR remoteness_ca>1",
    )
    check(
        "duplicate_points",
        f"SELECT count()-uniqExact(tuple(season,point_id)) n FROM {CASE}.idx_np",
    )
    check(
        "source_point_counts",
        f"SELECT abs((SELECT count() FROM {CASE}.idx_np)-(SELECT count() FROM {CASE}.reference_idx_np)) n",
    )
    check("region_counts", f"SELECT abs(count()-252) n FROM {CASE}.idx_region")
    check("atlas_counts", f"SELECT abs(count()-246) n FROM {ATLAS}.atlas_indices")
    for database, names in {
        "plexus_graph": [
            "nodes",
            "points",
            "locations",
            "region_codes",
            "region_points",
        ],
        "plexus_casechamp": ["market_cities", "stg_intercity", "manual_links_ru"],
    }.items():
        for name in names:
            fields = ",".join(
                "`" + row["name"] + "`"
                for row in store.rows(f"DESCRIBE TABLE {database}.{name}")
            )
            frozen = source["databases"][database]
            check(
                "frozen_" + name,
                f"SELECT (SELECT tuple(count(),groupBitXor(cityHash64(tuple({fields})))) FROM {database}.{name})!=(SELECT tuple(count(),groupBitXor(cityHash64(tuple({fields})))) FROM {frozen}.{name}) n",
            )
    check(
        "profile_count",
        f"SELECT abs((SELECT count() FROM {GRAPH}.road_costs)-(SELECT count() FROM {GRAPH}.ways)) n",
    )
    check(
        "profile_duplicates",
        f"SELECT count()-uniqExact(way_idx) n FROM {GRAPH}.road_costs",
    )
    check(
        "profile_coverage",
        f"SELECT count() n FROM {GRAPH}.ways w LEFT ANTI JOIN {GRAPH}.road_costs c ON w.way_idx=c.way_idx AND w.way_id=c.way_id",
    )
    check(
        "profile_values",
        f"SELECT count() n FROM {GRAPH}.road_costs WHERE NOT isFinite(effective_speed_kmh) OR effective_speed_kmh<=0 OR NOT isFinite(freeflow_speed_kmh) OR freeflow_speed_kmh<=0 OR (capacity_pcu_h IS NOT NULL AND (NOT isFinite(capacity_pcu_h) OR capacity_pcu_h<=0))",
    )
    check(
        "missing_index_values",
        f"SELECT count() n FROM {CASE}.idx_np WHERE hansen_idx IS NULL OR aria IS NULL OR remoteness_ca IS NULL",
    )
    check(
        "atlas_duplicates",
        f"SELECT count()-uniqExact(tuple(region_id,scenario)) n FROM {ATLAS}.atlas_indices",
    )
    check(
        "atlas_region_membership",
        f"SELECT count() n FROM {ATLAS}.atlas_indices a LEFT ANTI JOIN plexus_capacity_graph.region_codes c ON a.region_id=c.oktmo",
    )
    check(
        "atlas_scenarios",
        f"SELECT count() n FROM {ATLAS}.atlas_indices WHERE scenario NOT IN ('road','summer','winter')",
    )
    reference = state["reference"]
    normalization = reference["normalization_base"]
    sample = store.rows(f"""SELECT n.season,n.point_id,n.hansen_1h,n.hansen_2h,n.hansen_4h,n.hansen_idx,n.harris,
        coalesce(m.h1,0) h1,coalesce(m.h2,0) h2,coalesce(m.h4,0) h4,coalesce(m.harris_check,0) harris_check
        FROM (SELECT * FROM {CASE}.idx_np ORDER BY cityHash64(point_id,season) LIMIT 96) n
        LEFT JOIN (SELECT t.season,t.point_id,sum(c.population*exp(-log(2)*t.best_h)) h1,
        sum(c.population*exp(-log(2)/2*t.best_h)) h2,sum(c.population*exp(-log(2)/4*t.best_h)) h4,
        sum(c.population/(t.best_h+0.5)) harris_check
        FROM {CASE}.np_city_times t INNER JOIN {CASE}.market_cities c USING(city)
        WHERE tuple(t.season,t.point_id) IN (SELECT season,point_id FROM {CASE}.idx_np ORDER BY cityHash64(point_id,season) LIMIT 96)
        GROUP BY t.season,t.point_id) m ON n.season=m.season AND n.point_id=m.point_id""")
    if (
        len(sample) != 96
        or len({(row["season"], row["point_id"]) for row in sample}) != 96
    ):
        raise ValueError("Independent formula sample must contain 96 distinct points")
    for row in sample:
        for field, expected in [
            ("hansen_1h", row["h1"]),
            ("hansen_2h", row["h2"]),
            ("hansen_4h", row["h4"]),
            ("harris", row["harris_check"]),
            ("hansen_idx", row["h2"] / normalization * 100),
        ]:
            if not np.isclose(row[field], expected, rtol=2e-6, atol=1e-5):
                raise ValueError(
                    f"Independent matrix formula differs: {row['point_id']}: {field}"
                )
    computed = {
        (r["season"], r["region"]): r["runtime"]
        for r in state["stages"]["matrices"]["baselines"]
    }
    regions = store.rows(
        f"SELECT n.season,n.region,r.hansen_idx before,n.hansen_idx after,n.hansen_idx-r.hansen_idx delta,n.population FROM {CASE}.idx_region n INNER JOIN {CASE}.reference_idx_region r ON n.region=r.region AND n.season=r.season ORDER BY n.season,n.region"
    )
    errors = [
        abs(row["after"] - computed[(row["season"], row["region"])]) for row in regions
    ]
    if len(regions) != 252 or max(errors) > 1e-4:
        raise ValueError(
            "Regional aggregate differs from the runtime routing calculation"
        )
    with (folder / "regional-comparison.csv").open("w") as output:
        writer = csv.DictWriter(output, list(regions[0]))
        writer.writeheader()
        writer.writerows(regions)
    result = {
        "status": "passed",
        "date": datetime.now(UTC).isoformat(),
        "method": "road-capacity-v1",
        "source": source,
        "reference": reference,
        "artifact_version": candidate["artifact_version"],
        "checks": checks,
        "independent_matrix_sample": len(sample),
        "formulae_per_point": 5,
        "runtime_regional_baselines": len(computed),
        "max_runtime_hansen_error": max(errors),
        "source_regions": 84,
        "published_regions": 82,
        "seasons": ["road", "summer", "winter"],
        "confirmed_flow_profiles": state["stages"]["weights"][
            "confirmed_flow_profiles"
        ],
        "unknown_flow_policy": "free_flow",
        "table_plan": TABLES,
    }
    path = root / "docs/results/road-capacity-validation.json"
    path.write_text(json.dumps(result, ensure_ascii=False, indent=2, allow_nan=False))
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=Path.cwd())
    args = parser.parse_args()
    result = validate(CapacityStore(), args.root)
    print(json.dumps(result, ensure_ascii=False, allow_nan=False))


if __name__ == "__main__":
    main()
