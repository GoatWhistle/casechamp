CREATE TABLE IF NOT EXISTS plexus_normative.regional_origin_points
(
    snapshot String,
    region_id String,
    id String,
    name String,
    population Nullable(Int64),
    node Nullable(Int64),
    snap_km Nullable(Float64),
    latitude Nullable(Float64),
    longitude Nullable(Float64),
    source_region String
)
ENGINE = ReplacingMergeTree
ORDER BY (snapshot,region_id,id);

CREATE TABLE IF NOT EXISTS plexus_normative.regional_origin_snapshots
(
    revision String,
    created_at String,
    graph_revision String,
    boundary_sha256 String,
    source_sha256 String,
    assigned UInt64,
    outside UInt64,
    ambiguous UInt64
)
ENGINE = MergeTree
ORDER BY (created_at,revision);
