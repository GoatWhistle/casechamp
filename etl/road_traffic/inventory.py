import json

from road_traffic.attributes import normalize_way
from road_traffic.geography import RegionCoverage


def attributes(store, run_id, source):
    store.clear("road_attributes", run_id)
    columns = ["way_id", "way_idx", "highway", "ref", "name", "km", "source_tags"]
    fields = [
        "way_id",
        "way_idx",
        "highway",
        "lanes_total",
        "lanes_forward",
        "lanes_backward",
        "lanes_both_ways",
        "lanes_status",
        "oneway",
        "maxspeed_kmh",
        "maxspeed_forward_kmh",
        "maxspeed_backward_kmh",
        "direction_status",
        "maxspeed_status",
        "source_tags",
        "quality",
    ]
    count = 0
    for batch in store.batches(
        f"SELECT {','.join(columns)} FROM {source}.ways SETTINGS max_block_size=20000"
    ):
        rows = []
        for row in batch.to_pylist():
            item = normalize_way(row)
            rows.append({"run_id": run_id, **{key: item[key] for key in fields}})
        store.insert("road_attributes", rows)
        count += len(rows)
        if count % 200000 < len(rows):
            print(f"attributes: {count}", flush=True)
    expected = int(store.rows(f"SELECT count() n FROM {source}.ways")[0]["n"])
    actual = int(
        store.rows(
            f"SELECT count() n FROM {store.database}.road_attributes WHERE run_id='{run_id}'"
        )[0]["n"]
    )
    if count != expected or actual != expected:
        raise ValueError("Road attribute count mismatch")
    return count


def coverage(store, run_id, source):
    store.clear("coverage_parts", run_id)
    boundaries = store.rows(
        f"SELECT id,name,polygons FROM {source}.boundaries WHERE id IN (SELECT id FROM {source}.regions)"
    )
    geography = RegionCoverage(boundaries)
    known = {}
    for batch in store.batches(
        f"SELECT way_id,lanes_status,source_tags FROM {store.database}.road_attributes WHERE run_id='{run_id}' AND lanes_status!='missing'"
    ):
        for row in batch.to_pylist():
            tags = json.loads(row["source_tags"] or "{}")
            known[row["way_id"]] = (
                row["lanes_status"],
                int(
                    any(
                        k in tags
                        for k in [
                            "lanes",
                            "lanes:forward",
                            "lanes:backward",
                            "lanes:both_ways",
                        ]
                    )
                ),
            )
    count = 0
    outside = 0
    for batch in store.batches(
        f"SELECT way_id,highway,coordinates FROM {source}.road_lines WHERE highway!='ferry' SETTINGS max_block_size=10000"
    ):
        rows = []
        for line in batch.to_pylist():
            status, has_lanes = known.get(line["way_id"], ("missing", 0))
            pieces = geography.measure(line["coordinates"])
            outside += not bool(pieces)
            rows.extend(
                {
                    "run_id": run_id,
                    "region_id": region,
                    "way_id": line["way_id"],
                    "km": km,
                    "highway": line["highway"],
                    "lanes_status": status,
                    "has_lanes": has_lanes,
                }
                for region, km in pieces
            )
        store.insert("coverage_parts", rows)
        count += batch.num_rows
        if count % 100000 < batch.num_rows:
            print(f"geometry: {count}; outside atlas: {outside}", flush=True)
    return {
        "lines": count,
        "outside_atlas_lines": outside,
        "boundary_repairs": geography.repairs,
    }
