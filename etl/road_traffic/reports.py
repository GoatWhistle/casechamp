import csv
import json
from datetime import UTC, datetime

MAJOR = "replaceAll(highway,'_link','') IN ('motorway','trunk','primary','secondary','tertiary')"


def report(store, run_id, source, output, root):
    store.clear("regional_coverage", run_id)
    regions = store.rows(f"SELECT id,name FROM {source}.regions ORDER BY id")
    if len(regions) != 82:
        raise ValueError(f"Expected Atlas82, found {len(regions)}")
    coverage = {}
    for label, predicate in [("all", "1"), ("major", MAJOR)]:
        query = f"""SELECT region_id,uniqExact(way_id) ways,sum(p.km) km,
            uniqExactIf(way_id,has_lanes=1) tagged_ways,
            sumIf(p.km,has_lanes=1) tagged_km,
            uniqExactIf(way_id,lanes_status='valid') valid_ways,
            sumIf(p.km,lanes_status='valid') valid_km
            FROM {store.database}.coverage_parts AS p
            WHERE run_id='{run_id}' AND {predicate} GROUP BY region_id"""
        for row in store.rows(query):
            coverage.setdefault(row["region_id"], {}).update(
                {label + "_" + k: v for k, v in row.items() if k != "region_id"}
            )
    observations = {
        r["region_id"]: r
        for r in store.rows(f"""SELECT region_id,count() observations,countIf(value IS NOT NULL) numeric_values,
        countIf(value IS NULL) missing_values,
        uniqExact(JSONExtractString(record,'site')) sites,
        groupUniqArray(period) periods,uniqExact(source_id) sources FROM {store.database}.traffic_observations
        WHERE run_id='{run_id}' GROUP BY region_id""")
    }
    confirmed = {
        r["region_id"]: int(r["n"])
        for r in store.rows(f"""SELECT o.region_id,uniqExact(m.observation_id) n
        FROM {store.database}.graph_matches m INNER JOIN {store.database}.traffic_observations o
        ON m.run_id=o.run_id AND m.observation_id=o.observation_id
        WHERE m.run_id='{run_id}' AND m.status='confirmed' GROUP BY o.region_id""")
    }
    discovery = root / "datasets/additional/road-traffic/regional-source-checks.json"
    registry = json.loads(discovery.read_text()) if discovery.exists() else []
    checked = {r["region_id"]: r for r in registry}
    rows = []
    for region in regions:
        item = {"region_id": region["id"], "name": region["name"]}
        for label in ["all", "major"]:
            for key in [
                "ways",
                "km",
                "tagged_ways",
                "tagged_km",
                "valid_ways",
                "valid_km",
            ]:
                item[label + "_" + key] = coverage.get(region["id"], {}).get(
                    label + "_" + key, 0
                )
            for key in ["ways", "tagged_ways", "valid_ways"]:
                item[label + "_" + key] = int(item[label + "_" + key])
            length = float(item[label + "_km"])
            item[label + "_valid_length_share"] = (
                float(item[label + "_valid_km"]) / length if length else None
            )
        obs = observations.get(region["id"], {})
        item.update(
            observations=int(obs.get("observations", 0)),
            sources=int(obs.get("sources", 0)),
            confirmed_observations=confirmed.get(region["id"], 0),
        )
        item.update(
            numeric_values=int(obs.get("numeric_values", 0)),
            missing_values=int(obs.get("missing_values", 0)),
            sites=int(obs.get("sites", 0)),
            periods=obs.get("periods", []),
            source_check_status=checked.get(region["id"], {}).get(
                "owner_check_status", "not_checked"
            ),
            dataset_status=checked.get(region["id"], {}).get(
                "dataset_status", "not_checked"
            ),
        )
        item["flow_status"] = (
            "source_observations_available" if item["numeric_values"] else "unknown"
        )
        if item["numeric_values"]:
            item["dataset_status"] = "numerical_source_values_available"
        rows.append(item)
    store.insert(
        "regional_coverage",
        [
            {
                "run_id": run_id,
                "region_id": r["region_id"],
                "record": json.dumps(r, ensure_ascii=False),
            }
            for r in rows
        ],
    )
    stored = store.rows(
        f"SELECT region_id,record FROM {store.database}.regional_coverage WHERE run_id='{run_id}' ORDER BY region_id"
    )
    if [json.loads(r["record"]) for r in stored] != rows:
        raise ValueError("Stored report readback mismatch")
    with (output / "regional-coverage.csv").open("w") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    result = {
        "run_id": run_id,
        "created_at": datetime.now(UTC).isoformat(),
        "regions": rows,
        "source_registry_present": bool(registry),
        "method": "OSM geometry km; separated carriageways separately; shared polygon boundary owned by smallest region ID; absence of measurements is unknown flow",
        "source_snapshot": source,
        "active_graph_correspondence": json.loads(
            (
                root
                / "datasets/additional/road-traffic/active-graph-correspondence.json"
            ).read_text()
        )
        if (
            root / "datasets/additional/road-traffic/active-graph-correspondence.json"
        ).exists()
        else None,
    }
    (output / "regional-coverage.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2)
    )
    return {
        "regions": len(rows),
        "observations": sum(r["observations"] for r in rows),
        "confirmed_observations": sum(r["confirmed_observations"] for r in rows),
    }
