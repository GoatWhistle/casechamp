import pyarrow as pa
from app.domain.road_cost import evaluate_road

PROFILE_DDL = """way_idx Int32,way_id Int64,highway String,surface Nullable(String),
lanes_total Nullable(UInt16),lanes_forward Nullable(UInt16),lanes_backward Nullable(UInt16),
oneway Nullable(String),posted_speed_kmh Nullable(Float64),hourly_flow_pcu Nullable(Float64),
flow_verified Bool,lane_data_usable Bool,flow_source String,flow_period String,hourly_flow_scope String,is_ferry Bool,
source_speed_kmh Nullable(Float64),effective_speed_kmh Float64,freeflow_speed_kmh Float64,
capacity_pcu_h Nullable(Float64),lane_basis String,capacity_basis String,flow_basis String,method_version String"""


def profile(row):
    usable = row.get("lanes_status") in {"valid", "missing", None, ""}
    lane = {
        key: row.get(key)
        if isinstance(row.get(key), int)
        and not isinstance(row.get(key), bool)
        and row.get(key) >= 0
        else None
        for key in ["lanes_total", "lanes_forward", "lanes_backward"]
    }
    oneway = row.get("oneway")
    if (oneway or "").strip().lower() not in {
        "",
        "unknown",
        "forward",
        "reverse",
        "bidirectional",
        "yes",
        "true",
        "1",
        "-1",
        "no",
        "false",
        "0",
    }:
        usable = False
    if row.get("lanes_both_ways") and not all(
        row.get(key) for key in ["lanes_forward", "lanes_backward"]
    ):
        usable = False
    inputs = dict(
        length_km=max(0, row.get("km") or 0),
        highway=row.get("highway") or "road",
        surface=row.get("surface"),
        **lane,
        oneway=oneway,
        posted_speed_kmh=row.get("posted_speed_kmh"),
        hourly_flow_pcu=None,
        flow_verified=False,
        lane_data_usable=usable,
        flow_source="",
        flow_period="",
        hourly_flow_scope="directional",
        is_ferry=bool(row.get("is_ferry")),
        source_speed_kmh=row.get("source_speed_kmh"),
    )
    try:
        cost = evaluate_road(**inputs)
    except ValueError:
        inputs["lane_data_usable"] = False
        cost = evaluate_road(**inputs)
    inputs.pop("length_km")
    inputs.update(
        way_id=int(row["way_id"]),
        way_idx=int(row["way_idx"]),
        effective_speed_kmh=(
            max(0, row.get("km") or 0) / cost.travel_hours
            if cost.travel_hours
            else cost.speed_kmh
        ),
        freeflow_speed_kmh=cost.speed_kmh,
        capacity_pcu_h=cost.capacity_pcu_h,
        lane_basis=cost.lane_basis,
        capacity_basis=cost.capacity_basis,
        flow_basis=cost.flow_basis,
        method_version=cost.method_version,
    )
    return inputs


def profile_schema():
    types = {
        "Int32": pa.int32(),
        "Int64": pa.int64(),
        "String": pa.string(),
        "UInt16": pa.uint16(),
        "Float64": pa.float64(),
        "Bool": pa.bool_(),
    }
    fields = []
    for field in PROFILE_DDL.replace("\n", "").split(","):
        name, kind = field.strip().split()
        nullable = kind.startswith("Nullable(")
        kind = kind.removeprefix("Nullable(").removesuffix(")")
        fields.append(pa.field(name, types[kind], nullable=nullable))
    return pa.schema(fields)


def replace_weights(store):
    runs = store.rows(
        "SELECT run_id FROM plexus_traffic.runs FINAL WHERE status='completed' ORDER BY updated DESC LIMIT 1"
    )
    if len(runs) != 1:
        raise ValueError("A completed road-traffic input run is required")
    run_id = runs[0]["run_id"]
    confirmed = store.rows(
        f"SELECT count() n FROM plexus_traffic.graph_matches WHERE run_id='{run_id}' AND status='confirmed'"
    )
    if int(confirmed[0]["n"]):
        raise ValueError(
            "Confirmed flows require explicit directional hourly-PCU profile review before legacy aggregation"
        )
    target = "plexus_capacity_graph.road_costs"
    loading = target + "__loading"
    store.execute(f"DROP TABLE IF EXISTS {loading}")
    store.execute(
        f"CREATE TABLE {loading} ({PROFILE_DDL}) ENGINE=MergeTree ORDER BY way_idx"
    )
    count = 0
    query = f"""SELECT w.way_idx,w.way_id,w.highway,w.surface,coalesce(nullIf(nullIf(a.oneway,'unknown'),''),w.oneway) oneway,w.is_ferry,w.km,
        w.speed_kmh source_speed_kmh,a.lanes_total,a.lanes_forward,a.lanes_backward,
        a.lanes_status,a.lanes_both_ways,a.maxspeed_kmh posted_speed_kmh
        FROM plexus_capacity_graph.ways w LEFT JOIN
        (SELECT way_id,lanes_total,lanes_forward,lanes_backward,lanes_both_ways,oneway,lanes_status,maxspeed_kmh
         FROM plexus_traffic.road_attributes WHERE run_id='{run_id}') a ON w.way_id=a.way_id
        SETTINGS max_block_size=20000,max_threads=2,join_algorithm='grace_hash'"""
    for batch in store.batches(query):
        rows = [profile(row) for row in batch.to_pylist()]
        store.insert_arrow(loading, pa.Table.from_pylist(rows, schema=profile_schema()))
        count += len(rows)
        if count % 200000 < len(rows):
            print(f"capacity profiles: {count}", flush=True)
    expected = int(
        store.rows("SELECT count() n FROM plexus_capacity_graph.ways")[0]["n"]
    )
    if count != expected:
        raise ValueError("Road-cost profile count mismatch")
    if store.rows(f"EXISTS TABLE {target}")[0]["result"]:
        store.replace(loading, target)
    else:
        store.execute(f"RENAME TABLE {loading} TO {target}")
    for table, column, expression in [
        ("ways", "speed_kmh", "c.effective_speed_kmh"),
        ("edges", "h", "CAST(w.km/c.effective_speed_kmh,'Float32')"),
        ("road_lines", "speed_kmh", "c.effective_speed_kmh"),
    ]:
        target = "plexus_capacity_graph." + table
        loading = store.fresh(target)
        fields = [r["name"] for r in store.rows(f"DESCRIBE TABLE {target}")]
        expressions = [
            expression + " AS " + field if field == column else "w.`" + field + "`"
            for field in fields
        ]
        store.execute(
            f"INSERT INTO {loading} SELECT {','.join(expressions)} FROM {target} w INNER JOIN plexus_capacity_graph.road_costs c ON w.way_idx=c.way_idx"
            if table != "road_lines"
            else f"INSERT INTO {loading} SELECT {','.join(expressions)} FROM {target} w INNER JOIN plexus_capacity_graph.road_costs c ON w.way_id=c.way_id"
        )
        before = int(store.rows(f"SELECT count() n FROM {target}")[0]["n"])
        after = int(store.rows(f"SELECT count() n FROM {loading}")[0]["n"])
        if before != after:
            raise ValueError("Weighted graph row count changed")
        store.replace(loading, target)
    return {
        "ways": count,
        "traffic_run_id": run_id,
        "confirmed_flow_profiles": 0,
        "unknown_flow_policy": "free_flow",
        "method_version": "road-capacity-v1",
    }
